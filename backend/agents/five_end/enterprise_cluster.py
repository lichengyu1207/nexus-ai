"""
企业经营端智能体集群模块
Enterprise Cluster Module

实现估价智能体、企业报告智能体、客户画像智能体、风控智能体
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class ValuationMethod(Enum):
    MARKET_COMPARISON = "market_comparison"
    INCOME = "income"
    COST = "cost"
    HYPOTHETICAL_DEVELOPMENT = "hypothetical_development"
    MIXED = "mixed"


class RiskCategory(Enum):
    MARKET_RISK = "market_risk"
    CREDIT_RISK = "credit_risk"
    OPERATIONAL_RISK = "operational_risk"
    COMPLIANCE_RISK = "compliance_risk"
    REPUTATION_RISK = "reputation_risk"


class CustomerSegment(Enum):
    FIRST_TIME_BUYER = "first_time_buyer"
    INVESTOR = "investor"
    UPGRADER = "upgrader"
    DOWNSIZER = "downsizer"
    COMMERCIAL = "commercial"


@dataclass
class ValuationRequest:
    request_id: str
    property_id: str
    property_type: str
    location: Dict[str, str]
    area: float
    features: Dict[str, Any]
    purpose: str
    requested_by: str
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "property_id": self.property_id,
            "property_type": self.property_type,
            "location": self.location,
            "area": self.area,
            "features": self.features,
            "purpose": self.purpose,
            "requested_by": self.requested_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ValuationResult:
    result_id: str
    request_id: str
    estimated_value: float
    value_range: Tuple[float, float]
    method: ValuationMethod
    confidence: float
    comparables: List[Dict[str, Any]]
    adjustments: Dict[str, float]
    market_analysis: Dict[str, Any]
    generated_at: datetime
    generated_by: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "request_id": self.request_id,
            "estimated_value": self.estimated_value,
            "value_range": list(self.value_range),
            "method": self.method.value,
            "confidence": self.confidence,
            "comparables": self.comparables,
            "adjustments": self.adjustments,
            "market_analysis": self.market_analysis,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
        }


@dataclass
class CustomerProfile:
    profile_id: str
    customer_id: str
    segment: CustomerSegment
    preferences: Dict[str, Any]
    budget_range: Tuple[float, float]
    preferred_locations: List[str]
    transaction_history: List[str]
    risk_score: float
    lifetime_value: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "customer_id": self.customer_id,
            "segment": self.segment.value,
            "preferences": self.preferences,
            "budget_range": list(self.budget_range),
            "preferred_locations": self.preferred_locations,
            "transaction_history": self.transaction_history,
            "risk_score": self.risk_score,
            "lifetime_value": self.lifetime_value,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class RiskAssessment:
    assessment_id: str
    entity_id: str
    entity_type: str
    risk_category: RiskCategory
    risk_score: float
    risk_factors: List[Dict[str, Any]]
    mitigation_suggestions: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "risk_category": self.risk_category.value,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors,
            "mitigation_suggestions": self.mitigation_suggestions,
            "created_at": self.created_at.isoformat(),
        }


class BaseEnterpriseAgent:
    """企业经营智能体基类"""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        energy: float = 100.0,
        max_energy: float = 200.0
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.energy = energy
        self.max_energy = max_energy
        self.age = 0
        self.status = "idle"
        
        self.task_queue: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        
        self.stats = {
            "tasks_completed": 0,
            "energy_consumed": 0.0,
            "errors": 0,
        }
    
    def metabolize(self, base_rate: float = 0.1) -> float:
        consumption = base_rate * (1 + self.age * 0.01)
        self.energy = max(0, self.energy - consumption)
        self.stats["energy_consumed"] += consumption
        self.age += 1
        return consumption
    
    def gain_energy(self, amount: float) -> float:
        old_energy = self.energy
        self.energy = min(self.max_energy, self.energy + amount)
        return self.energy - old_energy
    
    def add_task(self, task: Dict[str, Any]):
        with self._lock:
            self.task_queue.append(task)
    
    def get_load(self) -> int:
        return len(self.task_queue)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "energy": self.energy,
            "age": self.age,
            "status": self.status,
            "queue_length": len(self.task_queue),
            **self.stats,
        }


class ValuationAgent(BaseEnterpriseAgent):
    """估价智能体"""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or f"valuation_{uuid.uuid4().hex[:8]}",
            agent_type="valuation",
            **kwargs
        )
        
        self.valuation_history: Dict[str, ValuationResult] = {}
        self.market_data: Dict[str, Any] = {}
        
        self.market_data_callback: Optional[Callable] = None
    
    def set_market_data_callback(self, callback: Callable):
        self.market_data_callback = callback
    
    async def valuate(
        self,
        request: ValuationRequest
    ) -> ValuationResult:
        self.status = "working"
        
        method = self._select_method(request)
        
        comparables = await self._find_comparables(request)
        
        adjustments = self._calculate_adjustments(request, comparables)
        
        estimated_value = await self._calculate_value(
            request, comparables, adjustments, method
        )
        
        confidence = self._calculate_confidence(comparables, adjustments)
        
        value_range = (
            estimated_value * (1 - (1 - confidence) * 0.5),
            estimated_value * (1 + (1 - confidence) * 0.5),
        )
        
        market_analysis = await self._analyze_market(request.location)
        
        result = ValuationResult(
            result_id=f"val_{int(time.time())}_{uuid.uuid4().hex[:6]}",
            request_id=request.request_id,
            estimated_value=estimated_value,
            value_range=value_range,
            method=method,
            confidence=confidence,
            comparables=comparables[:5],
            adjustments=adjustments,
            market_analysis=market_analysis,
            generated_at=datetime.now(),
            generated_by=self.agent_id,
        )
        
        self.valuation_history[result.result_id] = result
        
        self.gain_energy(5.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return result
    
    def _select_method(self, request: ValuationRequest) -> ValuationMethod:
        property_type = request.property_type
        
        if property_type in ["residential", "apartment"]:
            return ValuationMethod.MARKET_COMPARISON
        elif property_type in ["commercial", "office"]:
            return ValuationMethod.INCOME
        elif property_type in ["land", "development"]:
            return ValuationMethod.HYPOTHETICAL_DEVELOPMENT
        else:
            return ValuationMethod.MIXED
    
    async def _find_comparables(
        self,
        request: ValuationRequest
    ) -> List[Dict[str, Any]]:
        comparables = []
        
        for i in range(5):
            base_price = random.uniform(20000, 50000)
            comparables.append({
                "comparable_id": f"comp_{i}",
                "location": request.location,
                "area": request.area * random.uniform(0.9, 1.1),
                "price": base_price * request.area * random.uniform(0.95, 1.05),
                "price_per_sqm": base_price,
                "similarity": random.uniform(0.7, 0.95),
                "transaction_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            })
        
        return sorted(comparables, key=lambda x: x["similarity"], reverse=True)
    
    def _calculate_adjustments(
        self,
        request: ValuationRequest,
        comparables: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        adjustments = {}
        
        features = request.features
        
        adjustments["floor_level"] = features.get("floor", 1) * 0.01
        
        adjustments["orientation"] = 0.02 if features.get("orientation") == "south" else 0
        
        adjustments["age"] = -0.01 * features.get("building_age", 0)
        
        adjustments["parking"] = 0.03 if features.get("has_parking") else 0
        
        adjustments["renovation"] = features.get("renovation_level", 0) * 0.02
        
        return adjustments
    
    async def _calculate_value(
        self,
        request: ValuationRequest,
        comparables: List[Dict[str, Any]],
        adjustments: Dict[str, float],
        method: ValuationMethod
    ) -> float:
        if not comparables:
            return request.area * random.uniform(20000, 40000)
        
        avg_price_per_sqm = sum(c["price_per_sqm"] for c in comparables) / len(comparables)
        
        total_adjustment = sum(adjustments.values())
        
        adjusted_price_per_sqm = avg_price_per_sqm * (1 + total_adjustment)
        
        return adjusted_price_per_sqm * request.area
    
    def _calculate_confidence(
        self,
        comparables: List[Dict[str, Any]],
        adjustments: Dict[str, float]
    ) -> float:
        base_confidence = 0.7
        
        if comparables:
            avg_similarity = sum(c["similarity"] for c in comparables) / len(comparables)
            base_confidence += avg_similarity * 0.2
        
        adjustment_impact = sum(abs(v) for v in adjustments.values())
        base_confidence -= adjustment_impact * 0.1
        
        return max(0.5, min(0.95, base_confidence))
    
    async def _analyze_market(self, location: Dict[str, str]) -> Dict[str, Any]:
        return {
            "trend": random.choice(["up", "down", "stable"]),
            "avg_days_on_market": random.randint(30, 120),
            "inventory_level": random.choice(["low", "medium", "high"]),
            "buyer_demand": random.choice(["strong", "moderate", "weak"]),
        }
    
    def get_valuation(self, result_id: str) -> Optional[ValuationResult]:
        return self.valuation_history.get(result_id)


class EnterpriseReportAgent(BaseEnterpriseAgent):
    """企业报告智能体"""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or f"ent_report_{uuid.uuid4().hex[:8]}",
            agent_type="enterprise_report",
            **kwargs
        )
        
        self.reports: Dict[str, Dict[str, Any]] = {}
    
    async def generate_valuation_report(
        self,
        valuation_result: ValuationResult,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        self.status = "working"
        
        report_id = f"ent_rpt_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        report = {
            "report_id": report_id,
            "report_type": "valuation",
            "title": "房地产估价报告",
            "valuation_summary": valuation_result.to_dict(),
            "methodology": self._describe_methodology(valuation_result.method),
            "market_analysis": valuation_result.market_analysis,
            "assumptions": self._list_assumptions(valuation_result),
            "disclaimers": self._generate_disclaimers(),
            "appendix": additional_data or {},
            "generated_at": datetime.now().isoformat(),
            "generated_by": self.agent_id,
        }
        
        self.reports[report_id] = report
        
        self.gain_energy(3.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return report
    
    async def generate_portfolio_report(
        self,
        properties: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        self.status = "working"
        
        report_id = f"portfolio_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        total_value = sum(p.get("estimated_value", 0) for p in properties)
        
        report = {
            "report_id": report_id,
            "report_type": "portfolio",
            "title": "资产组合分析报告",
            "summary": {
                "total_properties": len(properties),
                "total_value": total_value,
                "avg_value": total_value / max(len(properties), 1),
            },
            "property_details": properties,
            "risk_analysis": self._analyze_portfolio_risk(properties),
            "recommendations": self._generate_portfolio_recommendations(properties),
            "generated_at": datetime.now().isoformat(),
        }
        
        self.reports[report_id] = report
        
        self.gain_energy(5.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return report
    
    def _describe_methodology(self, method: ValuationMethod) -> str:
        descriptions = {
            ValuationMethod.MARKET_COMPARISON: "市场比较法：通过分析近期类似物业的成交价格进行估价",
            ValuationMethod.INCOME: "收益法：基于物业预期收益进行估价",
            ValuationMethod.COST: "成本法：基于重置成本进行估价",
            ValuationMethod.HYPOTHETICAL_DEVELOPMENT: "假设开发法：基于开发后预期价值进行估价",
            ValuationMethod.MIXED: "综合法：结合多种方法进行估价",
        }
        return descriptions.get(method, "未知方法")
    
    def _list_assumptions(self, result: ValuationResult) -> List[str]:
        return [
            "市场条件保持稳定",
            "物业状况与描述一致",
            "无重大法律纠纷",
            "数据来源可靠",
        ]
    
    def _generate_disclaimers(self) -> List[str]:
        return [
            "本报告仅供参考，不构成投资建议",
            "估价结果受市场波动影响",
            "实际成交价格可能与估价存在差异",
        ]
    
    def _analyze_portfolio_risk(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "concentration_risk": "low",
            "market_risk": "medium",
            "liquidity_risk": "low",
        }
    
    def _generate_portfolio_recommendations(self, properties: List[Dict[str, Any]]) -> List[str]:
        return [
            "建议分散投资区域",
            "定期评估资产价值",
            "关注市场动态",
        ]
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self.reports.get(report_id)


class CustomerProfileAgent(BaseEnterpriseAgent):
    """客户画像智能体"""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or f"customer_{uuid.uuid4().hex[:8]}",
            agent_type="customer_profile",
            **kwargs
        )
        
        self.profiles: Dict[str, CustomerProfile] = {}
    
    async def create_profile(
        self,
        customer_id: str,
        initial_data: Dict[str, Any]
    ) -> CustomerProfile:
        self.status = "working"
        
        segment = self._classify_segment(initial_data)
        
        preferences = self._extract_preferences(initial_data)
        
        budget_range = self._estimate_budget(initial_data)
        
        preferred_locations = initial_data.get("preferred_locations", [])
        
        risk_score = self._calculate_risk_score(initial_data)
        
        lifetime_value = self._estimate_lifetime_value(initial_data, segment)
        
        profile = CustomerProfile(
            profile_id=f"prof_{uuid.uuid4().hex[:8]}",
            customer_id=customer_id,
            segment=segment,
            preferences=preferences,
            budget_range=budget_range,
            preferred_locations=preferred_locations,
            transaction_history=[],
            risk_score=risk_score,
            lifetime_value=lifetime_value,
            last_updated=datetime.now(),
        )
        
        self.profiles[profile.profile_id] = profile
        
        self.gain_energy(2.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return profile
    
    async def update_profile(
        self,
        profile_id: str,
        new_data: Dict[str, Any]
    ) -> Optional[CustomerProfile]:
        profile = self.profiles.get(profile_id)
        if not profile:
            return None
        
        self.status = "working"
        
        if "preferences" in new_data:
            profile.preferences.update(new_data["preferences"])
        
        if "transaction" in new_data:
            profile.transaction_history.append(new_data["transaction"])
        
        profile.risk_score = self._calculate_risk_score({
            "profile": profile,
            "new_data": new_data,
        })
        
        profile.lifetime_value = self._estimate_lifetime_value(
            {"profile": profile},
            profile.segment
        )
        
        profile.last_updated = datetime.now()
        
        self.gain_energy(1.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return profile
    
    def _classify_segment(self, data: Dict[str, Any]) -> CustomerSegment:
        if data.get("first_time_buyer"):
            return CustomerSegment.FIRST_TIME_BUYER
        elif data.get("investment_intent"):
            return CustomerSegment.INVESTOR
        elif data.get("current_property"):
            return CustomerSegment.UPGRADER
        else:
            return CustomerSegment.FIRST_TIME_BUYER
    
    def _extract_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "property_type": data.get("preferred_property_type", "residential"),
            "min_area": data.get("min_area", 50),
            "max_area": data.get("max_area", 200),
            "must_have": data.get("must_have_features", []),
            "nice_to_have": data.get("nice_to_have_features", []),
        }
    
    def _estimate_budget(self, data: Dict[str, Any]) -> Tuple[float, float]:
        income = data.get("annual_income", 200000)
        
        min_budget = income * 3
        max_budget = income * 6
        
        return (min_budget, max_budget)
    
    def _calculate_risk_score(self, data: Dict[str, Any]) -> float:
        base_score = 0.3
        
        if data.get("credit_issues"):
            base_score += 0.3
        
        if data.get("stable_income"):
            base_score -= 0.1
        
        return max(0, min(1, base_score))
    
    def _estimate_lifetime_value(
        self,
        data: Dict[str, Any],
        segment: CustomerSegment
    ) -> float:
        base_values = {
            CustomerSegment.FIRST_TIME_BUYER: 50000,
            CustomerSegment.INVESTOR: 200000,
            CustomerSegment.UPGRADER: 100000,
            CustomerSegment.DOWNSIZER: 30000,
            CustomerSegment.COMMERCIAL: 300000,
        }
        
        return base_values.get(segment, 50000)
    
    def get_profile(self, profile_id: str) -> Optional[CustomerProfile]:
        return self.profiles.get(profile_id)
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        for profile in self.profiles.values():
            if profile.customer_id == customer_id:
                return profile
        return None


class RiskControlAgent(BaseEnterpriseAgent):
    """风控智能体"""
    
    def __init__(self, agent_id: str = None, **kwargs):
        super().__init__(
            agent_id=agent_id or f"risk_{uuid.uuid4().hex[:8]}",
            agent_type="risk_control",
            **kwargs
        )
        
        self.assessments: Dict[str, RiskAssessment] = {}
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
        }
    
    async def assess_risk(
        self,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any]
    ) -> RiskAssessment:
        self.status = "working"
        
        risk_factors = []
        total_risk = 0.0
        
        for category in RiskCategory:
            factor_score = await self._assess_category(entity_data, category)
            
            if factor_score > 0.3:
                risk_factors.append({
                    "category": category.value,
                    "score": factor_score,
                    "description": self._describe_risk(category, factor_score),
                })
            
            total_risk += factor_score * 0.2
        
        total_risk = min(1.0, total_risk)
        
        category = self._determine_category(total_risk)
        
        mitigations = self._generate_mitigations(risk_factors)
        
        assessment = RiskAssessment(
            assessment_id=f"risk_{int(time.time())}_{uuid.uuid4().hex[:6]}",
            entity_id=entity_id,
            entity_type=entity_type,
            risk_category=category,
            risk_score=total_risk,
            risk_factors=risk_factors,
            mitigation_suggestions=mitigations,
            created_at=datetime.now(),
        )
        
        self.assessments[assessment.assessment_id] = assessment
        
        self.gain_energy(3.0)
        self.stats["tasks_completed"] += 1
        self.status = "idle"
        
        return assessment
    
    async def _assess_category(
        self,
        data: Dict[str, Any],
        category: RiskCategory
    ) -> float:
        if category == RiskCategory.MARKET_RISK:
            return self._assess_market_risk(data)
        elif category == RiskCategory.CREDIT_RISK:
            return self._assess_credit_risk(data)
        elif category == RiskCategory.OPERATIONAL_RISK:
            return self._assess_operational_risk(data)
        elif category == RiskCategory.COMPLIANCE_RISK:
            return self._assess_compliance_risk(data)
        else:
            return self._assess_reputation_risk(data)
    
    def _assess_market_risk(self, data: Dict[str, Any]) -> float:
        score = 0.0
        
        if data.get("market_volatility", 0) > 0.1:
            score += 0.3
        
        if data.get("inventory_high", False):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_credit_risk(self, data: Dict[str, Any]) -> float:
        score = 0.0
        
        credit_score = data.get("credit_score", 700)
        if credit_score < 600:
            score += 0.4
        elif credit_score < 700:
            score += 0.2
        
        debt_ratio = data.get("debt_ratio", 0)
        if debt_ratio > 0.5:
            score += 0.3
        
        return min(1.0, score)
    
    def _assess_operational_risk(self, data: Dict[str, Any]) -> float:
        score = 0.0
        
        if data.get("system_issues"):
            score += 0.2
        
        if data.get("staff_turnover_high"):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_compliance_risk(self, data: Dict[str, Any]) -> float:
        score = 0.0
        
        if data.get("regulatory_issues"):
            score += 0.4
        
        if data.get("license_expired"):
            score += 0.3
        
        return min(1.0, score)
    
    def _assess_reputation_risk(self, data: Dict[str, Any]) -> float:
        score = 0.0
        
        if data.get("negative_reviews", 0) > 10:
            score += 0.3
        
        if data.get("complaints", 0) > 5:
            score += 0.2
        
        return min(1.0, score)
    
    def _determine_category(self, score: float) -> RiskCategory:
        if score >= self.risk_thresholds["high"]:
            return RiskCategory.MARKET_RISK
        elif score >= self.risk_thresholds["medium"]:
            return RiskCategory.CREDIT_RISK
        else:
            return RiskCategory.OPERATIONAL_RISK
    
    def _describe_risk(self, category: RiskCategory, score: float) -> str:
        level = "高" if score > 0.7 else "中" if score > 0.4 else "低"
        return f"{category.value}风险{level}（{score:.2f}）"
    
    def _generate_mitigations(self, factors: List[Dict[str, Any]]) -> List[str]:
        mitigations = []
        
        for factor in factors:
            category = factor["category"]
            
            if category == "market_risk":
                mitigations.append("建议分散投资，降低市场波动影响")
            elif category == "credit_risk":
                mitigations.append("建议加强客户信用审核")
            elif category == "operational_risk":
                mitigations.append("建议优化运营流程")
            elif category == "compliance_risk":
                mitigations.append("建议及时更新相关资质")
            elif category == "reputation_risk":
                mitigations.append("建议加强客户关系管理")
        
        return mitigations
    
    def get_assessment(self, assessment_id: str) -> Optional[RiskAssessment]:
        return self.assessments.get(assessment_id)


class EnterpriseCluster:
    """企业经营端智能体集群主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.valuation_agents: List[ValuationAgent] = []
        self.report_agents: List[EnterpriseReportAgent] = []
        self.customer_agents: List[CustomerProfileAgent] = []
        self.risk_agents: List[RiskControlAgent] = []
        
        self.blackboard: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        self._running = False
        self._maintenance_task = None
        
        self.stats = {
            "total_valuations": 0,
            "total_reports": 0,
            "total_profiles": 0,
            "total_assessments": 0,
        }
        
        self._init_agents()
    
    def _init_agents(self):
        for _ in range(3):
            self.valuation_agents.append(ValuationAgent())
        
        for _ in range(2):
            self.report_agents.append(EnterpriseReportAgent())
        
        for _ in range(2):
            self.customer_agents.append(CustomerProfileAgent())
        
        self.risk_agents.append(RiskControlAgent())
    
    async def start(self):
        self._running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
    
    def stop(self):
        self._running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
    
    async def _maintenance_loop(self):
        while self._running:
            try:
                for agent in self.valuation_agents:
                    agent.metabolize()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
    
    async def valuate_property(
        self,
        request: ValuationRequest
    ) -> ValuationResult:
        if self.valuation_agents:
            agent = min(self.valuation_agents, key=lambda a: a.get_load())
            result = await agent.valuate(request)
            self.stats["total_valuations"] += 1
            return result
        return None
    
    async def generate_report(
        self,
        report_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.report_agents:
            agent = min(self.report_agents, key=lambda a: a.get_load())
            
            if report_type == "valuation":
                result = data.get("valuation_result")
                if result:
                    report = await agent.generate_valuation_report(result, data.get("additional"))
                else:
                    report = None
            elif report_type == "portfolio":
                report = await agent.generate_portfolio_report(data.get("properties", []))
            else:
                report = None
            
            if report:
                self.stats["total_reports"] += 1
            return report
        return None
    
    async def create_customer_profile(
        self,
        customer_id: str,
        data: Dict[str, Any]
    ) -> CustomerProfile:
        if self.customer_agents:
            agent = min(self.customer_agents, key=lambda a: a.get_load())
            profile = await agent.create_profile(customer_id, data)
            self.stats["total_profiles"] += 1
            return profile
        return None
    
    async def assess_risk(
        self,
        entity_id: str,
        entity_type: str,
        data: Dict[str, Any]
    ) -> RiskAssessment:
        if self.risk_agents:
            assessment = await self.risk_agents[0].assess_risk(entity_id, entity_type, data)
            self.stats["total_assessments"] += 1
            return assessment
        return None
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        return {
            "cluster_stats": self.stats,
            "valuation_agents": [a.get_stats() for a in self.valuation_agents],
            "report_agents": [a.get_stats() for a in self.report_agents],
            "customer_agents": [a.get_stats() for a in self.customer_agents],
            "risk_agents": [a.get_stats() for a in self.risk_agents],
        }
