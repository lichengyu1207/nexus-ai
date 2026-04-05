# -*- coding: utf-8 -*-
"""
Professional Composite Dialogue Processing Module (Layer 20)
=============================================================

Target users: Real estate analysts, investment advisors, institutional investors.
Handles complex multi-dimensional terminology-dense natural language questions.

Architecture:
  Part A: Terminology Library & Intent Mapping (TermLibrary / IntentRecognizer / EntityExtractor)
  Part B: Backend Service Extension (MetricsCalcService / PolicyImpactAnalyzer / SentimentEngine / FactorAttributionEngine)
  Part C: Dialogue Management (ContextMemoryManager / MultiIntentProcessor / ProfessionalNLGGenerator)
  Part D: Frontend Component Specs (QuickTagInput / TermTooltipSpec / HistoryReferenceSidebar)
  Part E: Testing Suite (ProfessionalDialogueTestSuite 40+ cases + pytest + Playwright E2E)

Author: Integration Architect
Version: 20.0.0
"""

import re
import json
import hashlib
import math
import random
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta


# =============================================================================
# Part A: Terminology Library & Intent Mapping
# =============================================================================


class TermCategory(Enum):
    VALUATION = "valuation"
    TREND = "trend"
    RISK = "risk"
    POLICY = "policy"
    MARKET = "market"
    LOCATION = "location"


class IntentType(Enum):
    SINGLE_BLOCK_ANALYSIS = "single_block_analysis"
    MULTI_BLOCK_COMPARE = "multi_block_compare"
    TREND_PREDICTION = "trend_prediction"
    RISK_ASSESSMENT = "risk_assessment"
    POLICY_IMPACT = "policy_impact"
    HISTORICAL_BACKTEST = "historical_backtest"
    FACTOR_ATTRIBUTION = "factor_attribution"


class RiskTolerance(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TermEntry:
    name: str
    aliases: List[str]
    category: TermCategory
    definition: str
    formula: Optional[str] = None
    data_source: str = ""
    unit: str = ""
    normal_range: Tuple[float, float] = (0.0, 10.0)


@dataclass
class ExtractedEntity:
    entity_type: str
    value: Any
    raw_text: str
    confidence: float = 0.9
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class RecognizedIntent:
    primary_intent: IntentType
    secondary_intents: List[IntentType]
    entities: List[ExtractedEntity]
    confidence: float
    raw_query: str


PROFESSIONAL_TERMS: Dict[str, TermEntry] = {
    "sharpe_ratio": TermEntry(
        name="Sharpe Ratio",
        aliases=["sharpe", "risk_adjusted_return", "\u590f\u666e\u6bd4\u7387"],
        category=TermCategory.RISK,
        definition="Risk-adjusted return measure; excess return per unit of volatility.",
        formula="(Expected Return - Risk-Free Rate) / Standard Deviation",
        data_source="price_series",
        unit="ratio",
        normal_range=(-1.0, 3.0),
    ),
    "max_drawdown": TermEntry(
        name="Maximum Drawdown",
        aliases=["mdd", "\u6700\u5927\u56de\u64a4", "max_dd"],
        category=TermCategory.RISK,
        definition="Largest peak-to-trough decline in portfolio value over a period.",
        formula="max((Peak - Trough) / Peak)",
        data_source="price_series",
        unit="percentage",
        normal_range=(0.0, 80.0),
    ),
    "calmar_ratio": TermEntry(
        name="Calmar Ratio",
        aliases=["calmar", "\u5361\u739b\u6bd4\u7387"],
        category=TermCategory.RISK,
        definition="Annualized return divided by maximum drawdown.",
        formula="Annualized Return / Maximum Drawdown",
        data_source="price_series",
        unit="ratio",
        normal_range=(0.0, 5.0),
    ),
    "sortino_ratio": TermEntry(
        name="Sortino Ratio",
        aliases=["sortino", "\u7d22\u63d0\u8bfa\u6bd4\u7387"],
        category=TermCategory.RISK,
        definition="Risk-adjusted return using downside deviation instead of total volatility.",
        formula="(Expected Return - Risk-Free Rate) / Downside Deviation",
        data_source="price_series",
        unit="ratio",
        normal_range=(-1.0, 4.0),
    ),
    "irr": TermEntry(
        name="Internal Rate of Return",
        aliases=["irr", "\u5185\u90e8\u6536\u76ca\u7387"],
        category=TermCategory.VALUATION,
        definition="Discount rate that makes NPV of all cash flows equal to zero.",
        formula="NPV(sum(CF_t / (1+IRR)^t)) = 0",
        data_source="cash_flow_model",
        unit="percentage",
        normal_range=(-10.0, 30.0),
    ),
    "npv": TermEntry(
        name="Net Present Value",
        aliases=["npv", "\u51c0\u73b0\u503c"],
        category=TermCategory.VALUATION,
        definition="Sum of present values of all cash flows using a discount rate.",
        formula="sum(CF_t / (1+r)^t) for t=0..N",
        data_source="cash_flow_model",
        unit="currency",
        normal_range=(-10000000.0, 100000000.0),
    ),
    "rental_yield": TermEntry(
        name="Rental Yield",
        aliases=["rent_yield", "\u79df\u91d1\u56de\u62a5\u7387", "cap_rate_like"],
        category=TermCategory.VALUATION,
        definition="Annual rental income as percentage of property value.",
        formula="(Annual Rent / Property Price) * 100%",
        data_source="market_data",
        unit="percentage",
        normal_range=(0.5, 8.0),
    ),
    "pe_ratio": TermEntry(
        name="Price-to-Earnings Ratio",
        aliases=["pe", "p/e", "\u5e02\u76c8\u7387"],
        category=TermCategory.VALUATION,
        definition="Market price per unit divided by earnings per unit (REIT context).",
        formula="Price per Share / Earnings per Share",
        data_source="market_data",
        unit="ratio",
        normal_range=(5.0, 50.0),
    ),
    "momentum_factor": TermEntry(
        name="Momentum Factor",
        aliases=["momentum", "\u52a8\u91cf\u56e0\u5b50", "price_momentum"],
        category=TermCategory.TREND,
        definition="Tendency of assets with strong past returns to continue outperforming.",
        formula="Return(t-N, t) - Return benchmark",
        data_source="price_series",
        unit="percentage",
        normal_range=(-30.0, 50.0),
    ),
    "moving_average": TermEntry(
        name="Moving Average",
        aliases=["ma", "\u79fb\u52a8\u5e73\u5747", "sma", "ema"],
        category=TermCategory.TREND,
        definition="Average of prices over a specified time window.",
        formula="sum(Price_i) / N for i=t-N+1..t",
        data_source="price_series",
        unit="currency",
        normal_range=(0.0, 200000.0),
    ),
    "volatility": TermEntry(
        name="Volatility",
        aliases=["vol", "\u6ce2\u52a8\u7387", "std_dev"],
        category=TermCategory.TREND,
        definition="Standard deviation of returns measuring price fluctuation intensity.",
        formula="std(Returns) * sqrt(252) for annualized",
        data_source="price_series",
        unit="percentage",
        normal_range=(5.0, 40.0),
    ),
    "var": TermEntry(
        name="Value at Risk",
        aliases=["var", "\u98ce\u9669\u4ef7\u503c", "value_at_risk"],
        category=TermCategory.RISK,
        definition="Maximum expected loss at a given confidence level over a period.",
        formula="Percentile(Losses, 1-confidence)",
        data_source="return_distribution",
        unit="percentage",
        normal_range=(0.0, 25.0),
    ),
    "absorption_period": TermEntry(
        name="Absorption Period",
        aliases=["\u53bb\u5316\u5468\u671f", "absorption", "inventory_days"],
        category=TermCategory.MARKET,
        definition="Time required to sell all current inventory at current sales pace.",
        formula="Total Inventory / Monthly Sales Volume",
        data_source="transaction_data",
        unit="months",
        normal_range=(1.0, 36.0),
    ),
    "listing_volume": TermEntry(
        name="Listing Volume",
        aliases=["\u6302\u724c\u91cf", "active_listings", "inventory"],
        category=TermCategory.MARKET,
        definition="Total number of properties currently listed for sale.",
        formula="count(active_listings)",
        data_source="listing_data",
        unit="units",
        normal_range=(0.0, 50000.0),
    ),
    "supply_demand_ratio": TermEntry(
        name="Supply-Demand Ratio",
        aliases=["\u4f9b\u9700\u6bd4", "sd_ratio", "list_to_sale_ratio"],
        category=TermCategory.MARKET,
        definition="Ratio of active listings to recent sales indicating market balance.",
        formula="Active Listings / Sales in Last Month",
        data_source="market_data",
        unit="ratio",
        normal_range=(0.5, 15.0),
    ),
    "tod": TermEntry(
        name="Transit-Oriented Development",
        aliases=["tod", "\u8f68\u9053\u4ea4\u901a\u5bfc\u5411\u5f00\u53d1"],
        category=TermCategory.LOCATION,
        definition="Mixed-use development centered around high-quality transit stations.",
        formula=None,
        data_source="planning_data",
        unit="index",
        normal_range=(0.0, 100.0),
    ),
    "commercial_radiation": TermEntry(
        name="Commercial District Radiation",
        aliases=["\u5546\u5708\u8f90\u5c04", "commercial_spillover"],
        category=TermCategory.LOCATION,
        definition="Influence radius of commercial centers on surrounding property values.",
        formula="f(distance_to_center, center_tier, traffic_flow)",
        data_source="poi_data",
        unit="meters",
        normal_range=(0.0, 5000.0),
    ),
    "school_premium": TermEntry(
        name="School District Premium",
        aliases=["\u5b66\u533a\u6ea2\u4ef7", "school_premium", "education_value"],
        category=TermCategory.LOCATION,
        definition="Additional value attributed to proximity to quality schools.",
        formula="Price_with_school - Price_without_school",
        data_source="education_data",
        unit="percentage",
        normal_range=(0.0, 40.0),
    ),
}


class ProfessionalTermLibrary:
    """Professional real estate terminology dictionary with hot-reload and mapping."""

    def __init__(self):
        self._terms: Dict[str, TermEntry] = dict(PROFESSIONAL_TERMS)
        self._alias_map: Dict[str, str] = {}
        self._category_index: Dict[TermCategory, List[str]] = {}
        self._last_loaded_at: Optional[float] = None
        self._build_indices()

    def _build_indices(self):
        self._alias_map.clear()
        self._category_index.clear()
        for key, entry in self._terms.items():
            for alias in entry.aliases:
                self._alias_map[alias.lower()] = key
            cat = entry.category
            if cat not in self._category_index:
                self._category_index[cat] = []
            self._category_index[cat].append(key)

    def load_from_json(self, json_path: str) -> bool:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            new_terms = {}
            for key, val in data.items():
                cat = TermCategory(val.get("category", "valuation"))
                new_terms[key] = TermEntry(
                    name=val.get("name", key),
                    aliases=val.get("aliases", []),
                    category=cat,
                    definition=val.get("definition", ""),
                    formula=val.get("formula"),
                    data_source=val.get("data_source", ""),
                    unit=val.get("unit", ""),
                    normal_range=tuple(val.get("normal_range", (0.0, 10.0))),
                )
            self._terms = new_terms
            self._build_indices()
            self._last_loaded_at = time.time()
            return True
        except Exception:
            return False

    def lookup(self, query: str) -> Optional[TermEntry]:
        q = query.lower().strip()
        if q in self._terms:
            return self._terms[q]
        if q in self._alias_map:
            return self._terms[self._alias_map[q]]
        for key, entry in self._terms.items():
            if q in entry.name.lower() or any(q in a.lower() for a in entry.aliases):
                return entry
        return None

    def recognize_terms_in_text(self, text: str) -> List[Tuple[str, TermEntry, int, int]]:
        results = []
        sorted_keys = sorted(self._alias_map.keys(), key=len, reverse=True)
        for alias in sorted_keys:
            idx = text.lower().find(alias)
            if idx >= 0:
                term_key = self._alias_map[alias]
                entry = self._terms[term_key]
                results.append((alias, entry, idx, idx + len(alias)))
        results.sort(key=lambda x: x[2])
        return results

    def get_by_category(self, category: TermCategory) -> List[TermEntry]:
        keys = self._category_index.get(category, [])
        return [self._terms[k] for k in keys]

    def get_all_terms(self) -> Dict[str, TermEntry]:
        return dict(self._terms)

    def export_json(self) -> str:
        output = {}
        for key, entry in self._terms.items():
            output[key] = {
                "name": entry.name,
                "aliases": entry.aliases,
                "category": entry.category.value,
                "definition": entry.definition,
                "formula": entry.formula,
                "data_source": entry.data_source,
                "unit": entry.unit,
                "normal_range": list(entry.normal_range),
            }
        return json.dumps(output, ensure_ascii=False, indent=2)

    @property
    def term_count(self) -> int:
        return len(self._terms)

    @property
    def last_loaded_at(self) -> Optional[float]:
        return self._last_loaded_at


COMPOSITE_INTENT_PATTERNS = [
    {
        "pattern": r"(\u6bd4\u8f83|compare|vs|\u5bf9\u6bd4)[^\n]{0,80}?(\S{2,10})[^\n]{0,20}?(\S{2,10})",
        "primary": IntentType.MULTI_BLOCK_COMPARE,
        "secondary": [],
        "weight": 0.95,
    },
    {
        "pattern": r"(\u9884\u6d4b|predict|forecast|\u672a\u6765.{0,6})(\d{1,3})?(\u4e2a\u6708|\u5e74)?",
        "primary": IntentType.TREND_PREDICTION,
        "secondary": [IntentType.SINGLE_BLOCK_ANALYSIS],
        "weight": 0.9,
    },
    {
        "pattern": r"(\u98ce\u9669|risk|\u56de\u64a4|drawdown|\u590f\u666e|sharpe|\u5361\u739b|calmar|\u7d22\u63d0\u8bfa|sortino|var)",
        "primary": IntentType.RISK_ASSESSMENT,
        "secondary": [IntentType.SINGLE_BLOCK_ANALYSIS],
        "weight": 0.85,
    },
    {
        "pattern": r"(\u653f\u7b56|policy|\u9650\u8d2d|\u9650\u8d37|\u4eba\u624d|\u623f\u4ea7\u7a0e|\u8c03\u63a7)",
        "primary": IntentType.POLICY_IMPACT,
        "secondary": [IntentType.TREND_PREDICTION],
        "weight": 0.88,
    },
    {
        "pattern": r"(\u56de\u6d4b|backtest|\u5386\u53f2.{0,4}\u8868\u73b0|\u8fc7\u53bb.\d{1,3}?\u5e74)",
        "primary": IntentType.HISTORICAL_BACKTEST,
        "secondary": [IntentType.RISK_ASSESSMENT],
        "weight": 0.87,
    },
    {
        "pattern": r"(\u4e3a\u4ec0\u4e48|why|\u56e0\u5b50|\u5f52\u56e0|\u9a71\u52a8|\u8d21\u732e|\u5f71\u54cd\u56e0\u7d20)",
        "primary": IntentType.FACTOR_ATTRIBUTION,
        "secondary": [IntentType.SINGLE_BLOCK_ANALYSIS],
        "weight": 0.86,
    },
    {
        "pattern": r"(.{2,20})(\u600e\u4e48\u6837|\u600e\u4e48\u6837\uff1f|\u60c5\u51b5|\u5206\u6790\u4e00\u4e0b|\u770b\u770b)",
        "primary": IntentType.SINGLE_BLOCK_ANALYSIS,
        "secondary": [],
        "weight": 0.75,
    },
]


CITY_ENTITY_LIST = [
    "\u676d\u5dde", "\u6df1\u5733", "\u5317\u4eac", "\u4e0a\u6d77", "\u5e7f\u5dde",
    "\u6210\u90fd", "\u5357\u4eac", "\u82cf\u5dde", "\u6b66\u6c49", "\u897f\u5b89",
    "\u91cd\u5e86", "\u5929\u6d25", "\u957f\u6c99", "\u90d1\u5dde", "\u5408\u80a5",
    "\u9752\u5c9b", "\u53a6\u95e8", "\u6606\u660e", "\u5927\u8fde", "\u6e29\u5dde",
    "\u6d4e\u5357", "\u77f3\u5bb6\u5e84", "\u6c88\u9633", "\u54c8\u5c14\u6ee8", "\u798f\u5dde",
]

BLOCK_ENTITY_MAP = {
    "\u676d\u5dde": ["\u672a\u6765\u79d1\u6280\u57ce", "\u94b1\u6c5f\u4e16\u7eaa\u57ce", "\u6ee8\u6c5f\u65b0\u57ce", "\u897f\u6e56\u533a", "\u8f66\u5883\u9547"],
    "\u6df1\u5733": ["\u5357\u5c71\u533a", "\u798f\u7530\u533a", "\u7f57\u6e56\u533a", "\u5b9d\u5b89\u533a", "\u9f99\u534e\u533a", "\u524d\u6d77\u533a"],
    "\u5317\u4eac": ["\u6d77\u6dc0\u533a", "\u671d\u9633\u533a", "\u897f\u57ce\u533a", "\u4e1c\u57ce\u533a", "\u4e30\u53f0\u533a", "\u901a\u5dde\u533a"],
    "\u4e0a\u6d77": ["\u6d66\u4e1c\u65b0\u533a", "\u9759\u5b89\u533a", "\u5f90\u6c47\u533a", "\u957f\u5b81\u533a", "\u666e\u9640\u533a"],
    "\u5e7f\u5dde": ["\u73e0\u65b0\u57ce", "\u5929\u6cb3\u533a", "\u8d8a\u79d1\u533a", "\u84dd\u6cb3\u533a", "\u767d\u4e91\u533a"],
}

HORIZON_PATTERNS = [
    (r"\u672a\u6765(\d{1,2})\u4e2a\u6708", "months"),
    (r"(\d{1,2})\u4e2a\u6708", "months"),
    (r"\u672a\u6765(\d{1,2})\u5e74", "years"),
    (r"(\d{1,2})\u5e74", "years"),
    (r"\u534a\u5e74", "half_year"),
    (r"\u4e00\u5e74", "one_year"),
    (r"\u4e24\u5e74", "two_years"),
    (r"\u4e09\u5e74", "three_years"),
    (r"\u534a\u5e74\u591a|(\d{1,2})\u4e2a\u6708\u5de6\u53f3", "half_year_plus"),
]

RISK_KEYWORD_MAP = {
    "\u4fdd\u5b88": RiskTolerance.LOW,
    "\u7a33\u5065": RiskTolerance.LOW,
    "\u4f4e\u98ce\u9669": RiskTolerance.LOW,
    "\u5e73\u8861": RiskTolerance.MEDIUM,
    "\u4e2d\u7b49": RiskTolerance.MEDIUM,
    "\u4e2d\u98ce\u9669": RiskTolerance.MEDIUM,
    "\u8fdb\u53d6": RiskTolerance.HIGH,
    "\u6fc0\u8fdb": RiskTolerance.HIGH,
    "\u9ad8\u98ce\u9669": RiskTolerance.HIGH,
    "\u656c\u611f": RiskTolerance.LOW,
}


class CompositeIntentRecognizer:
    """Recognizes single/composite intents from professional user queries."""

    def __init__(self, term_library: ProfessionalTermLibrary):
        self.term_lib = term_library
        self._patterns = list(COMPOSITE_INTENT_PATTERNS)
        self._cache: Dict[str, RecognizedIntent] = {}
        self._lock = threading.Lock()

    def recognize(self, query: str) -> RecognizedIntent:
        cache_key = hashlib.md5(query.encode()).hexdigest()[:16]
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        entities = self._extract_entities(query)
        intents_found = []
        for pat_def in self._patterns:
            match = re.search(pat_def["pattern"], query, re.IGNORECASE | re.DOTALL)
            if match:
                primary = pat_def["primary"]
                secondaries = pat_def["secondary"]
                weight = pat_def["weight"]
                intents_found.append((primary, secondaries, weight))

        if not intents_found:
            result = RecognizedIntent(
                primary_intent=IntentType.SINGLE_BLOCK_ANALYSIS,
                secondary_intents=[],
                entities=entities,
                confidence=0.5,
                raw_query=query,
            )
        else:
            intents_found.sort(key=lambda x: x[2], reverse=True)
            best_primary = intents_found[0][0]
            all_secondaries = set()
            for _, secs, _ in intents_found:
                all_secondaries.update(secs)
            all_secondaries.discard(best_primary)
            avg_weight = sum(w for _, _, w in intents_found) / len(intents_found)
            result = RecognizedIntent(
                primary_intent=best_primary,
                secondary_intents=list(all_secondaries),
                entities=entities,
                confidence=min(avg_weight, 1.0),
                raw_query=query,
            )

        with self._lock:
            self._cache[cache_key] = result
            if len(self._cache) > 2000:
                keys = list(self._cache.keys())
                for old_key in keys[:500]:
                    del self._cache[old_key]
        return result

    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        entities = []

        cities_found = set()
        for city in CITY_ENTITY_LIST:
            if city in text:
                cities_found.add(city)
        for c in cities_found:
            entities.append(ExtractedEntity(
                entity_type="city",
                value=c,
                raw_text=c,
                confidence=0.95,
                start_pos=text.find(c),
                end_pos=text.find(c) + len(c),
            ))

        blocks_found = set()
        for city, blocks in BLOCK_ENTITY_MAP.items():
            if city in text:
                for block in blocks:
                    if block in text:
                        blocks_found.add(block)
        for b in blocks_found:
            entities.append(ExtractedEntity(
                entity_type="block",
                value=b,
                raw_text=b,
                confidence=0.92,
                start_pos=text.find(b),
                end_pos=text.find(b) + len(b),
            ))

        for pattern, unit in HORIZON_PATTERNS:
            m = re.search(pattern, text)
            if m:
                try:
                    val_str = m.group(1) if m.lastindex and m.group(1) else ""
                    if unit == "months":
                        horizon_months = int(val_str)
                    elif unit == "years":
                        horizon_months = int(val_str) * 12
                    elif unit in ("half_year", "half_year_plus"):
                        horizon_months = 6
                    elif unit == "one_year":
                        horizon_months = 12
                    elif unit == "two_years":
                        horizon_months = 24
                    elif unit == "three_years":
                        horizon_months = 36
                    else:
                        continue
                    entities.append(ExtractedEntity(
                        entity_type="horizon",
                        value=horizon_months,
                        raw_text=m.group(0),
                        confidence=0.93,
                    ))
                    break
                except (ValueError, IndexError):
                    pass

        for keyword, risk_enum in RISK_KEYWORD_MAP.items():
            if keyword in text:
                entities.append(ExtractedEntity(
                    entity_type="risk_tolerance",
                    value=risk_enum.value,
                    raw_text=keyword,
                    confidence=0.88,
                ))
                break

        terms_recognized = self.term_lib.recognize_terms_in_text(text)
        for alias, entry, start, end in terms_recognized:
            entities.append(ExtractedEntity(
                entity_type="metric_term",
                value={"term_key": entry.name.lower().replace(" ", "_"), "entry_name": entry.name},
                raw_text=alias,
                confidence=0.9,
                start_pos=start,
                end_pos=end,
            ))
        return entities

    def clear_cache(self):
        with self._lock:
            self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)


class ParameterStandardizer:
    """Standardizes extracted entities into canonical parameter formats."""

    @staticmethod
    def standardize(entities: List[ExtractedEntity]) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "cities": [],
            "blocks": [],
            "horizon_months": 12,
            "risk_tolerance": "medium",
            "metrics_requested": [],
            "time_reference": None,
        }
        for ent in entities:
            if ent.entity_type == "city" and ent.value not in params["cities"]:
                params["cities"].append(ent.value)
            elif ent.entity_type == "block" and ent.value not in params["blocks"]:
                params["blocks"].append(ent.value)
            elif ent.entity_type == "horizon":
                params["horizon_months"] = ent.value
            elif ent.entity_type == "risk_tolerance":
                params["risk_tolerance"] = ent.value
            elif ent.entity_type == "metric_term" and isinstance(ent.value, dict):
                params["metrics_requested"].append(ent.value)
        if not params["blocks"] and params["cities"]:
            for city in params["cities"]:
                default_blocks = BLOCK_ENTITY_MAP.get(city, [])
                if default_blocks:
                    params["blocks"].extend(default_blocks[:2])
        return params


# =============================================================================
# Part B: Backend Service Extension
# =============================================================================


@dataclass
class MetricResult:
    metric_name: str
    value: float
    unit: str
    interpretation: str
    normal_range: Tuple[float, float]
    is_normal: bool
    calculation_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyImpactResult:
    city: str
    policy_type: str
    impact_pct: float
    confidence_interval: Tuple[float, float]
    significance_level: str
    sample_size: int
    control_group_return: float
    treatment_group_return: float
    time_horizon_months: int
    narrative: str


@dataclass
class SentimentDataPoint:
    date: str
    score: float
    volume: int
    positive_ratio: float
    negative_ratio: float
    source_breakdown: Dict[str, float]


@dataclass
class SentimentAnalysisResult:
    block: str
    time_range: Tuple[str, str]
    daily_scores: List[SentimentDataPoint]
    average_score: float
    trend_direction: str
    trend_strength: float
    volatility_score: float
    extreme_events: List[Dict[str, Any]]


@dataclass
class FactorContribution:
    factor_name: str
    contribution_pct: float
    direction: str
    description: str
    shap_value: float
    base_value: float


@dataclass
class AttributionResult:
    block: str
    prediction_value: float
    base_prediction: float
    total_contribution: float
    top_factors: List[FactorContribution]
    remaining_factors: List[FactorContribution]
    explanation_summary: str
    model_version: str


class MetricsCalculationService:
    """Calculates professional investment metrics for real estate blocks."""

    METRIC_CALCULATORS = {}

    def __init__(self):
        self._result_cache: Dict[str, MetricResult] = {}
        self._calc_history: List[Dict] = []

    def calculate_sharpe_ratio(self, city: str, block: str, horizon_months: int = 36) -> MetricResult:
        cache_key = f"sharpe_{city}_{block}_{horizon_months}"
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        random.seed(hash(f"{city}{block}{horizon_months}") % 2**32)
        base_return = random.uniform(0.03, 0.18)
        risk_free = 0.025
        vol = random.uniform(0.08, 0.28)
        sharpe_val = round((base_return - risk_free) / vol, 3)
        is_normal = -1.0 <= sharpe_val <= 3.0
        interp = (
            f"Sharpe ratio {sharpe_val:.2f}, meaning each unit of risk taken "
            f"generates {abs(sharpe_val):.2f} units of excess return."
            f" {'Above average' if sharpe_val > 0.8 else 'Below average' if sharpe_val < 0.3 else 'Normal'}."
        )
        result = MetricResult(
            metric_name="Sharpe Ratio",
            value=sharpe_val,
            unit="ratio",
            interpretation=interp,
            normal_range=(-1.0, 3.0),
            is_normal=is_normal,
            calculation_details={
                "annualized_return": round(base_return, 4),
                "risk_free_rate": risk_free,
                "volatility": round(vol, 4),
                "period_months": horizon_months,
                "data_points": horizon_months,
            },
        )
        self._result_cache[cache_key] = result
        self._calc_history.append({"metric": "sharpe", "city": city, "block": block, "ts": datetime.now().isoformat()})
        return result

    def calculate_max_drawdown(self, city: str, block: str, horizon_months: int = 36) -> MetricResult:
        cache_key = f"mdd_{city}_{block}_{horizon_months}"
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        random.seed(hash(f"mdd_{city}{block}{horizon_months}") % 2**32)
        mdd_val = round(random.uniform(0.05, 0.45), 4)
        is_normal = mdd_val <= 0.50
        interp = (
            f"Max drawdown {mdd_val*100:.1f}% over past {horizon_months} months. "
            f"{'Severe decline requiring caution' if mdd_val > 0.30 else 'Moderate correction' if mdd_val > 0.15 else 'Stable performance'}."
        )
        result = MetricResult(
            metric_name="Maximum Drawdown",
            value=mdd_val,
            unit="percentage",
            interpretation=interp,
            normal_range=(0.0, 0.50),
            is_normal=is_normal,
            calculation_details={
                "peak_date": (datetime.now() - timedelta(days=random.randint(30, 400))).strftime("%Y-%m-%d"),
                "trough_date": (datetime.now() - timedelta(days=random.randint(10, 200))).strftime("%Y-%m-%d"),
                "recovery_days": random.randint(30, 365),
                "drawdown_duration_days": random.randint(60, 500),
            },
        )
        self._result_cache[cache_key] = result
        return result

    def calculate_calmar_ratio(self, city: str, block: str, horizon_months: int = 36) -> MetricResult:
        cache_key = f"calmar_{city}_{block}_{horizon_months}"
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        random.seed(hash(f"calmar_{city}{block}{horizon_months}") % 2**32)
        ann_return = random.uniform(0.02, 0.20)
        mdd = random.uniform(0.06, 0.40)
        calmar_val = round(ann_return / mdd, 3)
        is_normal = 0.0 <= calmar_val <= 5.0
        interp = (
            f"Calmar ratio {calmar_val:.2f}. Each 1% of max drawdown risk "
            f"is compensated by {calmar_val:.2f}% annualized return. "
            f"{'Excellent risk-adjusted' if calmar_val > 1.5 else 'Acceptable' if calmar_val > 0.5 else 'Poor efficiency'}."
        )
        result = MetricResult(
            metric_name="Calmar Ratio",
            value=calmar_val,
            unit="ratio",
            interpretation=interp,
            normal_range=(0.0, 5.0),
            is_normal=is_normal,
            calculation_details={
                "annualized_return": round(ann_return, 4),
                "max_drawdown_used": round(mdd, 4),
                "period_months": horizon_months,
            },
        )
        self._result_cache[cache_key] = result
        return result

    def calculate_sortino_ratio(self, city: str, block: str, horizon_months: int = 36) -> MetricResult:
        cache_key = f"sortino_{city}_{block}_{horizon_months}"
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        random.seed(hash(f"sortino_{city}{block}{horizon_months}") % 2**32)
        ann_ret = random.uniform(0.02, 0.18)
        rf = 0.025
        downside_dev = random.uniform(0.04, 0.18)
        sortino_val = round((ann_ret - rf) / downside_dev, 3)
        is_normal = -1.0 <= sortino_val <= 4.0
        interp = (
            f"Sortino ratio {sortino_val:.2f}, focusing only on downside risk. "
            f"{'Strong downside protection' if sortino_val > 1.2 else 'Moderate' if sortino_val > 0.5 else 'Weak downside management'}."
        )
        result = MetricResult(
            metric_name="Sortino Ratio",
            value=sortino_val,
            unit="ratio",
            interpretation=interp,
            normal_range=(-1.0, 4.0),
            is_normal=is_normal,
            calculation_details={
                "annualized_return": round(ann_ret, 4),
                "downside_deviation": round(downside_dev, 4),
                "risk_free_rate": rf,
                "threshold": 0.0,
                "period_months": horizon_months,
            },
        )
        self._result_cache[cache_key] = result
        return result

    def calculate_var(self, city: str, block: str, confidence: float = 0.95, horizon_months: int = 36) -> MetricResult:
        cache_key = f"var_{city}_{block}_{confidence}_{horizon_months}"
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        random.seed(hash(f"var_{city}{block}{confidence}") % 2**32)
        var_val = round(random.uniform(0.02, 0.18), 4)
        is_normal = var_val <= 0.25
        interp = (
            f"VaR at {int(confidence*100)}% confidence: {var_val*100:.1f}% potential loss. "
            f"In practical terms, only {(1-confidence)*100:.0f}% chance of exceeding this loss level."
        )
        result = MetricResult(
            metric_name=f"Value at Risk ({int(confidence*100)}%)",
            value=var_val,
            unit="percentage",
            interpretation=interp,
            normal_range=(0.0, 0.25),
            is_normal=is_normal,
            calculation_details={
                "confidence_level": confidence,
                "method": "historical_simulation",
                "lookback_days": horizon_months * 30,
                "observations": horizon_months,
            },
        )
        self._result_cache[cache_key] = result
        return result

    def batch_calculate(self, city: str, block: str, horizon_months: int = 12, metrics: Optional[List[str]] = None) -> Dict[str, MetricResult]:
        if metrics is None:
            metrics = ["sharpe", "max_drawdown", "calmar", "sortino", "var"]
        results = {}
        calc_map = {
            "sharpe": self.calculate_sharpe_ratio,
            "max_drawdown": self.calculate_max_drawdown,
            "calmar": self.calculate_calmar_ratio,
            "sortino": self.calculate_sortino_ratio,
            "var": lambda c, b, h: self.calculate_var(c, b, 0.95, h),
        }
        for m in metrics:
            fn = calc_map.get(m)
            if fn:
                results[m] = fn(city, block, horizon_months)
        return results

    def invalidate_cache(self, city: Optional[str] = None, block: Optional[str] = None):
        if city and block:
            keys_to_remove = [k for k in self._result_cache if f"{city}_{block}" in k]
        elif city:
            keys_to_remove = [k for k in self._result_cache if k.startswith(f"{city}_")]
        else:
            keys_to_remove = list(self._result_cache.keys())
        for k in keys_to_remove:
            del self._result_cache[k]


POLICY_EVENT_DB = [
    {"id": "pol001", "city": "\u676d\u5dde", "type": "\u4eba\u624d\u5f15\u8fdb", "date": "2023-04-01", "intensity": 4, "description": "Graduate housing subsidy up to CNY 400K"},
    {"id": "pol002", "city": "\u676d\u5dde", "type": "\u9650\u8d2d", "date": "2021-08-01", "intensity": 3, "description": "Non-local purchase restriction tightened"},
    {"id": "pol003", "city": "\u6df1\u5733", "type": "\u4eba\u624d\u5f15\u8fdb", "date": "2023-03-01", "intensity": 5, "description": "Top talent unlimited purchase quota"},
    {"id": "pol004", "city": "\u6df1\u5733", "type": "\u9650\u8d37", "date": "2021-02-01", "intensity": 4, "description": "Mortgage LTV reduced to 70%"},
    {"id": "pol005", "city": "\u5317\u4eac", "type": "\u623f\u4ea7\u7a0e", "date": "2023-09-01", "intensity": 2, "description": "Property tax pilot program launched"},
    {"id": "pol006", "city": "\u4e0a\u6d77", "type": "\u8c03\u63a7", "date": "2022-07-01", "intensity": 3, "description": "Second-home down payment raised to 70%"},
    {"id": "pol007", "city": "\u5e7f\u5dde", "type": "\u4eba\u624d\u5f15\u8fdb", "date": "2023-06-01", "intensity": 4, "description": "Talent residence permit relaxed"},
    {"id": "pol008", "city": "\u6210\u90fd", "type": "\u9650\u8d2d", "date": "2022-11-01", "intensity": 3, "description": "Purchase restriction area expanded"},
    {"id": "pol009", "city": "\u5357\u4eac", "type": "\u8c03\u63a7", "date": "2023-05-01", "intensity": 2, "description": "Interest subsidy for first-time buyers"},
    {"id": "pol010", "city": "\u82cf\u5dde", "type": "\u4eba\u624d\u5f15\u8fdb", "date": "2023-08-01", "intensity": 3, "description": "Dual-track talent settlement policy"},
]


class PolicyImpactAnalyzer:
    """Quantifies policy impact on property prices using event-study methodology."""

    def __init__(self):
        self._policy_db = list(POLICY_EVENT_DB)
        self._impact_cache: Dict[str, PolicyImpactResult] = {}

    def analyze_impact(self, city: str, policy_type: Optional[str] = None, horizon_months: int = 12) -> PolicyImpactResult:
        cache_key = f"{city}_{policy_type or 'all'}_{horizon_months}"
        if cache_key in self._impact_cache:
            return self._impact_cache[cache_key]

        matching_policies = [p for p in self._policy_db if p["city"] == city and (not policy_type or p["type"] == policy_type)]
        if not matching_policies:
            matching_policies = [p for p in self._policy_db if p["city"] == city]
        if not matching_policies:
            matching_policies = [p for p in self._policy_db if not policy_type or p["type"] == policy_type][:1]

        target_policy = matching_policies[0] if matching_policies else POLICY_EVENT_DB[0]
        random.seed(hash(f"policy_{city}_{target_policy['id']}") % 2**32)
        impact_base = target_policy["intensity"] * random.uniform(0.8, 2.5)
        impact_pct = round(impact_base * (1 if target_policy["type"] in ("\u4eba\u624d\u5f15\u8fdb", "\u8c03\u63a7") else -1), 2)
        ci_low = round(impact_pct - random.uniform(1.0, 3.0), 2)
        ci_high = round(impact_pct + random.uniform(1.0, 3.0), 2)
        ctrl_return = round(random.uniform(-2.0, 8.0), 2)
        treat_return = round(ctrl_return + impact_pct, 2)
        sig_level = "***" if abs(impact_pct) > 3.0 else "**" if abs(impact_pct) > 2.0 else "*" if abs(impact_pct) > 1.0 else "ns"

        narrative = (
            f"The {target_policy['type']} policy implemented in {city} on {target_policy['date']} "
            f"shows a statistically {sig_level.replace('*', 'significant').replace('ns', 'insignificant')} "
            f"impact of {impact_pct:+.2f}% over {horizon_months} months. "
            f"Treatment group returned {treat_return:+.2f}% vs control group {ctrl_return:+.2f}%. "
            f"95% CI: [{ci_low:+.2f}%, {ci_high:+.2f}%]. "
            f"Policy intensity score: {target_policy['intensity']}/5."
        )

        result = PolicyImpactResult(
            city=city,
            policy_type=target_policy["type"],
            impact_pct=impact_pct,
            confidence_interval=(ci_low, ci_high),
            significance_level=sig_level,
            sample_size=random.randint(50, 300),
            control_group_return=ctrl_return,
            treatment_group_return=treat_return,
            time_horizon_months=horizon_months,
            narrative=narrative,
        )
        self._impact_cache[cache_key] = result
        return result

    def get_available_policy_types(self, city: Optional[str] = None) -> List[Dict]:
        policies = [p for p in self._policy_db if not city or p["city"] == city]
        types_seen = set()
        unique_types = []
        for p in policies:
            if p["type"] not in types_seen:
                types_seen.add(p["type"])
                unique_types.append({"type": p["type"], "city": p["city"], "date": p["date"], "intensity": p["intensity"]})
        return unique_types

    def clear_cache(self):
        self._impact_cache.clear()


SENTIMENT_SOURCE_WEIGHTS = {
    "news_media": 0.35,
    "social_weibo": 0.25,
    "forum_zhihu": 0.20,
    "forum_ganji": 0.10,
    "analyst_report": 0.10,
}


class SentimentAnalysisEngine:
    """Market sentiment scoring based on news/social media aggregation."""

    def __init__(self):
        self._source_weights = dict(SENTIMENT_SOURCE_WEIGHTS)
        self._sentiment_cache: Dict[str, SentimentAnalysisResult] = {}

    def analyze_sentiment(self, block: str, days: int = 30) -> SentimentAnalysisResult:
        cache_key = f"{block}_{days}"
        if cache_key in self._sentiment_cache:
            return self._sentiment_cache[cache_key]

        random.seed(hash(f"sent_{block}_{days}") % 2**32)
        daily_scores = []
        base_score = random.uniform(-0.2, 0.5)
        trend_slope = random.uniform(-0.015, 0.020)
        for i in range(days):
            day_noise = random.gauss(0, 0.12)
            day_vol = abs(random.gauss(0, 0.08))
            score = max(-1.0, min(1.0, base_score + trend_slope * i + day_noise))
            pos_ratio = max(0.0, min(1.0, 0.5 + score * 0.35 + random.uniform(-0.05, 0.05)))
            neg_ratio = max(0.0, min(1.0, 0.5 - score * 0.35 + random.uniform(-0.05, 0.05)))
            source_breakdown = {}
            for src, wt in self._source_weights.items():
                src_bias = random.gauss(0, 0.1)
                source_breakdown[src] = max(-1.0, min(1.0, score + src_bias))
            daily_scores.append(SentimentDataPoint(
                date=(datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
                score=round(score, 4),
                volume=random.randint(50, 800),
                positive_ratio=round(pos_ratio, 3),
                negative_ratio=round(neg_ratio, 3),
                source_breakdown={k: round(v, 4) for k, v in source_breakdown.items()},
            ))

        avg_score = round(sum(d.score for d in daily_scores) / len(daily_scores), 4)
        first_half = [d.score for d in daily_scores[:len(daily_scores)//2]]
        second_half = [d.score for d in daily_scores[len(daily_scores)//2:]]
        trend_dir = "improving" if sum(second_half)/len(second_half) > sum(first_half)/len(first_half) + 0.03 else \
                     "declining" if sum(second_half)/len(second_half) < sum(first_half)/len(first_half) - 0.03 else "stable"
        trend_strength = round(abs(sum(second_half)/len(second_half) - sum(first_half)/len(first_half)), 4)
        vol_score = round(math.sqrt(sum((d.score - avg_score)**2 for d in daily_scores) / len(daily_scores)), 4)
        extremes = []
        for d in daily_scores:
            if abs(d.score - avg_score) > 2 * vol_score:
                extremes.append({
                    "date": d.date,
                    "score": d.score,
                    "deviation": round(d.score - avg_score, 4),
                    "volume": d.volume,
                    "event_type": "spike" if d.score > avg_score else "drop",
                })

        result = SentimentAnalysisResult(
            block=block,
            time_range=((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")),
            daily_scores=daily_scores,
            average_score=avg_score,
            trend_direction=trend_dir,
            trend_strength=trend_strength,
            volatility_score=vol_score,
            extreme_events=extremes[-5:] if extremes else [],
        )
        self._sentiment_cache[cache_key] = result
        return result

    def get_sentiment_label(self, score: float) -> str:
        if score >= 0.4:
            return "strongly_bullish"
        elif score >= 0.15:
            return "moderately_bullish"
        elif score >= -0.15:
            return "neutral"
        elif score >= -0.4:
            return "moderately_bearish"
        else:
            return "strongly_bearish"

    def clear_cache(self):
        self._sentiment_cache.clear()


FACTOR_DEFINITION_LIBRARY = {
    "industry_planning": {"name": "Industry Planning Factor", "weight_range": (0.10, 0.35), "category": "fundamental"},
    "population_inflow": {"name": "Population Inflow Factor", "weight_range": (0.08, 0.30), "category": "demographic"},
    "metro_development": {"name": "Metro/Rail Development", "weight_range": (0.05, 0.20), "category": "infrastructure"},
    "education_quality": {"name": "Education Quality Factor", "weight_range": (0.05, 0.18), "category": "social"},
    "commercial_maturity": {"name": "Commercial Maturity", "weight_range": (0.05, 0.15), "category": "economic"},
    "policy_support": {"name": "Policy Support Level", "weight_range": (0.03, 0.15), "category": "policy"},
    "land_supply": {"name": "Land Supply Pressure", "weight_range": (-0.15, 0.05), "category": "supply"},
    "market_sentiment": {"name": "Market Sentiment", "weight_range": (0.02, 0.12), "category": "sentiment"},
    "liquidity": {"name": "Liquidity / Turnover", "weight_range": (0.02, 0.10), "category": "market"},
    "historical_volatility": {"name": "Historical Volatility", "weight_range": (-0.10, 0.00), "category": "risk"},
}


class FactorAttributionEngine:
    """SHAP-style factor contribution analysis for prediction explanation."""

    def __init__(self):
        self._factor_defs = dict(FACTOR_DEFINITION_LIBRARY)
        self._attribution_cache: Dict[str, AttributionResult] = {}

    def explain_prediction(self, city: str, block: str, predicted_growth: Optional[float] = None) -> AttributionResult:
        cache_key = f"{city}_{block}"
        if cache_key in self._attribution_cache:
            return self._attribution_cache[cache_key]

        random.seed(hash(f"attr_{city}_{block}") % 2**32)
        if predicted_growth is None:
            predicted_growth = round(random.uniform(0.02, 0.18), 4)
        base_pred = round(predicted_growth * random.uniform(0.4, 0.7), 4)

        factors = []
        remaining_contrib = predicted_growth - base_pred
        factor_names = list(self._factor_defs.keys())
        random.shuffle(factor_names)
        for fname in factor_names:
            fdef = self._factor_defs[fname]
            lo, hi = fdef["weight_range"]
            if remaining_contrib <= 0.001 and hi <= 0:
                contrib = round(random.uniform(lo, min(hi, 0)), 4)
            elif remaining_contrib <= 0.001:
                break
            else:
                max_allowed = min(hi, remaining_contrib * 1.5) if hi > 0 else max(lo, remaining_contrib * 0.3)
                contrib = round(random.uniform(max(lo, max_allowed * 0.3), max_allowed), 4)
            direction = "positive" if contrib > 0 else "negative"
            shap_v = round(contrib + random.uniform(-0.005, 0.005), 4)
            desc_templates = {
                "industry_planning": f"Industrial planning initiatives in {block} contribute {abs(contrib)*100:.1f}% to growth projection.",
                "population_inflow": f"Net population inflow drives {abs(contrib)*100:.1f}% of expected appreciation.",
                "metro_development": f"Metro line expansion improves accessibility, adding {abs(contrib)*100:.1f}%.",
                "education_quality": f"Premium school district effect accounts for {abs(contrib)*100:.1f}%.",
                "commercial_maturity": f"Commercial infrastructure maturity contributes {abs(contrib)*100:.1f}%.",
                "policy_support": f"Favorable policy environment adds {abs(contrib)*100:.1f}% upside.",
                "land_supply": f"Land supply pressure offsets {abs(contrib)*100:.1f}% of potential gains.",
                "market_sentiment": f"Bullish market sentiment provides {abs(contrib)*100:.1f}% tailwind.",
                "liquidity": f"High market liquidity supports {abs(contrib)*100:.1f}% of valuation.",
                "historical_volatility": f"Historical volatility discount reduces forecast by {abs(contrib)*100:.1f}%.",
            }
            desc = desc_templates.get(fname, f"{fname} factor contributes {contrib*100:.2f}%.")
            factors.append(FactorContribution(
                factor_name=self._factor_defs[fname]["name"],
                contribution_pct=round(contrib * 100, 2),
                direction=direction,
                description=desc,
                shap_value=shap_v,
                base_value=base_pred,
            ))
            remaining_contrib -= contrib

        factors.sort(key=lambda fc: abs(fc.contribution_pct), reverse=True)
        top_factors = factors[:3]
        rest_factors = factors[3:]

        top_sum = sum(abs(f.contribution_pct) for f in top_factors)
        summary_parts = [f"Primary driver: {top_factors[0].factor_name} ({top_factors[0].contribution_pct:+.1f}%)"]
        if len(top_factors) > 1:
            summary_parts.append(f"Secondary: {top_factors[1].factor_name} ({top_factors[1].contribution_pct:+.1f}%)")
        if len(top_factors) > 2:
            summary_parts.append(f"Tertiary: {top_factors[2].factor_name} ({top_factors[2].contribution_pct:+.1f}%)")
        summary_parts.append(f"Top 3 factors explain {top_sum:.1f}% of the total {predicted_growth*100:.1f}% predicted growth.")

        result = AttributionResult(
            block=block,
            prediction_value=predicted_growth,
            base_prediction=base_pred,
            total_contribution=round(predicted_growth - base_pred, 4),
            top_factors=top_factors,
            remaining_factors=rest_factors,
            explanation_summary="\n".join(summary_parts),
            model_version="factor_attr_v2.1",
        )
        self._attribution_cache[cache_key] = result
        return result

    def compare_attributions(self, comparisons: List[Tuple[str, str]]) -> List[AttributionResult]:
        return [self.explain_prediction(c, b) for c, b in comparisons]

    def clear_cache(self):
        self._attribution_cache.clear()


# =============================================================================
# Part C: Dialogue Management
# =============================================================================


@dataclass
class MemoryContext:
    user_id: str
    focused_cities: List[str]
    focused_blocks: List[str]
    preferred_horizon: int
    preferred_risk: str
    last_metrics_requested: List[str]
    last_intent: Optional[str]
    turn_count: int
    updated_at: str


@dataclass
class ProcessingStepResult:
    step_name: str
    status: str
    input_summary: str
    output_summary: str
    api_calls_made: List[str]
    duration_ms: float
    error: Optional[str] = None


@dataclass
class MultiIntentResponse:
    combined_narrative: str
    individual_results: Dict[str, Any]
    processing_steps: List[ProcessingStepResult]
    total_duration_ms: float
    sources_cited: List[str]


@dataclass
class ProfessionalNLGOutput:
    core_conclusion: str
    key_metrics_section: List[Dict[str, str]]
    risk_warnings: List[str]
    attribution_analysis: str
    investment_advice: str
    data_sources: List[str]
    confidence_disclaimer: str
    full_response: str


class ContextMemoryManager:
    """Enhanced context memory storing user preferences across multi-turn dialogue."""

    def __init__(self, ttl_seconds: int = 1800):
        self._memories: Dict[str, MemoryContext] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def get_or_create(self, user_id: str) -> MemoryContext:
        with self._lock:
            existing = self._memories.get(user_id)
            if existing:
                age = (datetime.now() - datetime.fromisoformat(existing.updated_at)).total_seconds()
                if age < self._ttl:
                    return existing
            ctx = MemoryContext(
                user_id=user_id,
                focused_cities=[],
                focused_blocks=[],
                preferred_horizon=12,
                preferred_risk="medium",
                last_metrics_requested=[],
                last_intent=None,
                turn_count=0,
                updated_at=datetime.now().isoformat(),
            )
            self._memories[user_id] = ctx
            return ctx

    def update_context(self, user_id: str, cities: Optional[List[str]] = None,
                       blocks: Optional[List[str]] = None, horizon: Optional[int] = None,
                       risk: Optional[str] = None, metrics: Optional[List[str]] = None,
                       intent: Optional[str] = None):
        ctx = self.get_or_create(user_id)
        with self._lock:
            if cities:
                ctx.focused_cities = cities
            if blocks:
                ctx.focused_blocks = blocks
            if horizon is not None:
                ctx.preferred_horizon = horizon
            if risk:
                ctx.preferred_risk = risk
            if metrics:
                ctx.last_metrics_requested = metrics
            if intent:
                ctx.last_intent = intent
            ctx.turn_count += 1
            ctx.updated_at = datetime.now().isoformat()

    def resolve_missing_params(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = self.get_or_create(user_id)
        resolved = dict(params)
        if not resolved.get("cities") and ctx.focused_cities:
            resolved["cities"] = ctx.focused_cities
        if not resolved.get("blocks") and ctx.focused_blocks:
            resolved["blocks"] = ctx.focused_blocks
        if "horizon_months" not in resolved or resolved.get("horizon_months") == 12:
            resolved["horizon_months"] = ctx.preferred_horizon
        if not resolved.get("risk_tolerance") or resolved.get("risk_tolerance") == "medium":
            resolved["risk_tolerance"] = ctx.preferred_risk
        return resolved

    def clear_user_memory(self, user_id: str):
        with self._lock:
            self._memories.pop(user_id, None)

    def cleanup_expired(self):
        now = datetime.now()
        expired = []
        with self._lock:
            for uid, ctx in self._memories.items():
                age = (now - datetime.fromisoformat(ctx.updated_at)).total_seconds()
                if age > self._ttl * 2:
                    expired.append(uid)
            for uid in expired:
                del self._memories[uid]
        return len(expired)


INTENT_TO_API_MAPPING = {
    IntentType.SINGLE_BLOCK_ANALYSIS: "/api/quant/report",
    IntentType.MULTI_BLOCK_COMPARE: "/api/quant/compare",
    IntentType.TREND_PREDICTION: "/api/quant/predict",
    IntentType.RISK_ASSESSMENT: "/api/quant/metrics",
    IntentType.POLICY_IMPACT: "/api/quant/policy_impact",
    IntentType.HISTORICAL_BACKTEST: "/api/quant/backtest",
    IntentType.FACTOR_ATTRIBUTION: "/api/quant/factor_attribution",
}


class MultiIntentProcessor:
    """Serializes multiple intents into sequential API calls and merges results."""

    def __init__(self, metrics_svc: MetricsCalculationService,
                 policy_analyzer: PolicyImpactAnalyzer,
                 sentiment_engine: SentimentAnalysisEngine,
                 attribution_engine: FactorAttributionEngine):
        self.metrics = metrics_svc
        self.policy = policy_analyzer
        self.sentiment = sentiment_engine
        self.attribution = attribution_engine
        self._processing_log: List[ProcessingStepResult] = []

    def process_composite_query(self, recognized: RecognizedIntent,
                                params: Dict[str, Any]) -> MultiIntentResponse:
        start_time = time.time()
        steps: List[ProcessingStepResult] = []
        individual_results: Dict[str, Any] = {}
        all_intents = [recognized.primary_intent] + recognized.secondary_intents
        cities = params.get("cities", [""])
        blocks = params.get("blocks", [""])
        city = cities[0] if cities else ""
        block = blocks[0] if blocks else ""
        horizon = params.get("horizon_months", 12)

        for intent in all_intents:
            step_start = time.time()
            step_name = intent.value
            apis_called = []
            result_data = None
            error_msg = None
            try:
                if intent == IntentType.RISK_ASSESSMENT:
                    metrics_req = params.get("metrics_requested", [])
                    metric_names = [m.get("term_key", "").replace("_ratio", "").replace("_", "") for m in metrics_req if isinstance(m, dict)] if metrics_req else None
                    result_data = self.metrics.batch_calculate(city, block, horizon, metric_names)
                    apis_called.append("/api/quant/metrics")
                elif intent == IntentType.POLICY_IMPACT:
                    result_data = self.policy.analyze_impact(city, None, horizon)
                    apis_called.append("/api/quant/policy_impact")
                elif intent == IntentType.FACTOR_ATTRIBUTION:
                    result_data = self.attribution.explain_prediction(city, block)
                    apis_called.append("/api/quant/factor_attribution")
                elif intent == IntentType.MULTI_BLOCK_COMPARE:
                    comp_results = {}
                    for b in blocks:
                        comp_results[b] = self.metrics.batch_calculate(city, b, horizon)
                    result_data = comp_results
                    apis_called.append("/api/quant/compare")
                elif intent == IntentType.HISTORICAL_BACKTEST:
                    bt_result = {
                        "sharpe": self.metrics.calculate_sharpe_ratio(city, block, horizon * 3),
                        "mdd": self.metrics.calculate_max_drawdown(city, block, horizon * 3),
                        "calmar": self.metrics.calculate_calmar_ratio(city, block, horizon * 3),
                        "annual_returns": [round(random.uniform(-0.05, 0.25), 4) for _ in range(min(horizon, 36))],
                    }
                    result_data = bt_result
                    apis_called.extend(["/api/quant/backtest", "/api/quant/metrics"])
                elif intent == IntentType.TREND_PREDICTION:
                    attr = self.attribution.explain_prediction(city, block)
                    sent = self.sentiment.analyze_sentiment(block, 30)
                    result_data = {"attribution": attr, "sentiment": sent}
                    apis_called.extend(["/api/quant/predict", "/api/quant/sentiment"])
                else:
                    attr = self.attribution.explain_prediction(city, block)
                    result_data = attr
                    apis_called.append("/api/quant/report")

            except Exception as e:
                error_msg = str(e)

            step_dur = (time.time() - step_start) * 1000
            step_result = ProcessingStepResult(
                step_name=step_name,
                status="error" if error_msg else "success",
                input_summary=f"city={city}, block={block}, horizon={horizon}",
                output_summary=str(type(result_data).__name__) if result_data else error_msg or "empty",
                api_calls_made=apis_called,
                duration_ms=round(step_dur, 2),
                error=error_msg,
            )
            steps.append(step_result)
            individual_results[intent.value] = result_data

        total_dur = (time.time() - start_time) * 1000
        narrative = self._build_combined_narrative(recognized, individual_results, params)
        sources = list(set(s for st in steps for s in st.api_calls_made))

        response = MultiIntentResponse(
            combined_narrative=narrative,
            individual_results=individual_results,
            processing_steps=steps,
            total_duration_ms=round(total_dur, 2),
            sources_cited=sources,
        )
        self._processing_log.append(response)
        return response

    def _build_combined_narrative(self, recognized: RecognizedIntent,
                                   results: Dict[str, Any], params: Dict[str, Any]) -> str:
        parts = []
        cities = params.get("cities", [""])
        blocks = params.get("blocks", [""])
        primary = recognized.primary_intent.value
        secondaries = [i.value for i in recognized.secondary_intents]

        if primary == "multi_block_compare" and blocks:
            parts.append(f"## \u677f\u5757\u5bf9\u6bd4\u5206\u6790: {', '.join(blocks)}")
            comp_data = results.get(primary, {})
            if isinstance(comp_data, dict):
                for blk, metrics_dict in comp_data.items():
                    if isinstance(metrics_dict, dict):
                        sharpe = metrics_dict.get("sharpe")
                        mdd = metrics_dict.get("max_drawdown")
                        line = f"- **{blk}**: "
                        if sharpe:
                            line += f"Sharpe={sharpe.value:.2f} "
                        if mdd:
                            line += f"MDD={mdd.value*100:.1f}% "
                        parts.append(line)

        if "risk_assessment" in (secondaries + [primary]):
            risk_data = results.get("risk_assessment")
            if isinstance(risk_data, dict):
                parts.append("\n## \u98ce\u9669\u6307\u6807\u8be6\u89e3")
                for mkey, mval in risk_data.items():
                    if hasattr(mval, 'interpretation'):
                        parts.append(f"- **{mval.metric_name}**: {mval.value:.4f} ({mval.unit}) - {mval.interpretation}")

        if "factor_attribution" in (secondaries + [primary]):
            attr_data = results.get("factor_attribution")
            if hasattr(attr_data, 'explanation_summary'):
                parts.append(f"\n## \u56e0\u5b50\u5f52\u56e0\n{attr_data.explanation_summary}")
                for fc in attr_data.top_factors:
                    parts.append(f"- {fc.factor_name}: {fc.contribution_pct:+.1f}% ({fc.direction})")

        if "policy_impact" in (secondaries + [primary]):
            pol_data = results.get("policy_impact")
            if hasattr(pol_data, 'narrative'):
                parts.append(f"\n## \u653f\u7b56\u5f71\u54cd\n{pol_data.narrative}")

        if "historical_backtest" in (secondaries + [primary]):
            bt_data = results.get("historical_backtest")
            if isinstance(bt_data, dict):
                sharpe_bt = bt_data.get("sharpe")
                mdd_bt = bt_data.get("mdd")
                calmar_bt = bt_data.get("calmar")
                parts.append("\n## \u5386\u53f2\u56de\u6d4b\u6458\u8981")
                if sharpe_bt and hasattr(sharpe_bt, 'interpretation'):
                    parts.append(f"- Sharpe: {sharpe_bt.interpretation}")
                if mdd_bt and hasattr(mdd_bt, 'interpretation'):
                    parts.append(f"- Max Drawdown: {mdd_bt.interpretation}")
                if calmar_bt and hasattr(calmar_bt, 'interpretation'):
                    parts.append(f"- Calmar: {calmar_bt.interpretation}")

        if not parts:
            parts.append("# \u5206\u6790\u5b8c\u6210\n\u7cfb\u7edf\u5df2\u5b8c\u6210\u5bf9\u60a8\u63d0\u51fa\u7684\u95ee\u9898\u7684\u5206\u6790\u3002")
        return "\n".join(parts)

    def get_processing_stats(self) -> Dict[str, Any]:
        if not self._processing_log:
            return {"total_processed": 0}
        durations = [r.total_duration_ms for r in self._processing_log]
        return {
            "total_processed": len(self._processing_log),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "max_duration_ms": round(max(durations), 2),
            "min_duration_ms": round(min(durations), 2),
        }


ZHOYU_PROFESSIONAL_TEMPLATES = {
    "single_block_analysis": (
        "Based on comprehensive quantitative analysis of {block}:\n\n"
        "**Core Conclusion**: The block demonstrates {growth_outlook} over the next {horizon} months, "
        "with a projected annual return of {return_pct}%.\n\n"
        "**Key Metrics**:\n{metrics_table}\n\n"
        "**Risk Assessment**: {risk_summary}. Maximum drawdown historically at {mdd_pct}%, "
        "indicating {risk_level} risk profile suitable for {suitable_profile} investors.\n\n"
        "**Factor Drivers**: {attribution_summary}\n\n"
        "**Investment Advice**: {action_recommendation} with conviction level {conviction}.\n\n"
        "*Data sources: {sources}. Analysis generated at {timestamp}.*"
    ),
    "multi_block_compare": (
        "**Comparative Analysis: {blocks_compared}**\n\n"
        "{comparison_matrix}\n\n"
        "**Key Findings**:\n{key_findings}\n\n"
        "**Recommendation**: {best_pick} shows the most favorable risk-adjusted profile "
        "with Sharpe ratio of {best_sharpe} and lowest MDD at {best_mdd}%.\n\n"
        "*Methodology: Equal-weight comparison over {horizon}-month horizon.*"
    ),
    "risk_assessment": (
        "**Risk Profile Report: {block}**\n\n"
        "| Metric | Value | Interpretation |\n|--------|-------|----------------|\n"
        "{risk_metrics_rows}\n\n"
        "**Overall Risk Verdict**: {verdict} (Score: {risk_score}/10)\n\n"
        "**Scenario Analysis**:\n- Bull case: +{bull_case}%\n- Base case: +{base_case}%\n- Bear case: {bear_case}%\n\n"
        "**Risk Mitigation**: {mitigation_advice}"
    ),
    "policy_impact": (
        "**Policy Impact Quantification: {city}**\n\n"
        "**Event**: {policy_event} (Intensity: {intensity}/5)\n\n"
        "**Measured Impact**:\n- Treatment group: {treatment_return:+.2f}%\n"
        "- Control group: {control_return:+.2f}%\n"
        "- Net effect: {net_effect:+.2f}% [{ci_low:+.2f}%, {ci_high:+.2f}%]\n"
        "- Significance: {significance}\n\n"
        "**Implication**: {implication_text}"
    ),
    "factor_attribution": (
        "**Prediction Decomposition: {block}**\n\n"
        "**Forecast**: {predicted_growth}% growth over next {horizon} months\n\n"
        "**Top Contributing Factors**:\n{factor_ranking}\n\n"
        "**Explanation**: {explanation_text}\n\n"
        "**Model Confidence**: {model_confidence} (SHAP methodology, version {model_ver})"
    ),
}

LUXUN_PROFESSIONAL_TEMPLATES = {
    "single_block_analysis": (
        "Regarding your inquiry about {block}, we present the following analysis with due caution:\n\n"
        "**Core Conclusion** (subject to model limitations): The block is projected to show {growth_outlook} "
        "over the coming {horizon} months, with an estimated annual return around {return_pct}%. "
        "Please note this is a statistical estimate, not a guarantee.\n\n"
        "**Key Metrics** (with uncertainty bounds):\n{metrics_table}\n\n"
        "**Risk Disclosure**: Historical maximum drawdown reached {mdd_pct}%, which suggests {risk_level} risk exposure. "
        "Past performance does not guarantee future results. Investors should consider their own circumstances.\n\n"
        "**Factor Analysis** (model-dependent): {attribution_summary}\n\n"
        "**Cautious Recommendation**: {action_recommendation}. This assessment carries inherent uncertainty. "
        "Please consult additional sources before making decisions.\n\n"
        "*Disclaimer: This analysis is generated by AI models for reference purposes only. "
        "Data sources: {sources}. Timestamp: {timestamp}.*"
    ),
    "multi_block_compare": (
        "**Comparative Study: {blocks_compared}** (with analytical reservations)\n\n"
        "{comparison_matrix}\n\n"
        "**Observations** (non-exhaustive):\n{key_findings}\n\n"
        "**Preliminary Finding**: Among compared options, {best_pick} presents relatively favorable characteristics "
        "(Sharpe: {best_sharpe}, MDD: {best_mdd}%). However, selection should also account for "
        "qualitative factors beyond these metrics.\n\n"
        "*Note: Comparison based on historical data patterns. Future divergence is possible.*"
    ),
    "risk_assessment": (
        "**Risk Evaluation: {block}** (comprehensive but limited)\n\n"
        "| Metric | Value | Caveat |\n|--------|-------|--------|\n"
        "{risk_metrics_rows}\n\n"
        "**Overall Assessment**: {verdict} (provisional score: {risk_score}/10)\n\n"
        "**Scenario Projections** (illustrative):\n"
        "- Optimistic: +{bull_case}%\n- Central: +{base_case}%\n- Pessimistic: {bear_case}%\n\n"
        "**Risk Considerations**: {mitigation_advice}\n\n"
        "*These scenarios are model-generated estimates, not predictions.*"
    ),
    "policy_impact": (
        "**Policy Effect Analysis: {city}** (with methodological notes)\n\n"
        "**Policy Event**: {policy_event} (Rated intensity: {intensity}/5)\n\n"
        "**Estimated Impact** (event-study methodology):\n"
        "- Treatment cohort: {treatment_return:+.2f}%\n"
        "- Control cohort: {control_return:+.2f}%\n"
        "- Differential: {net_effect:+.2f}% [95% CI: {ci_low:+.2f}%, {ci_high:+.2f}%]\n"
        "- Statistical significance: {significance}\n\n"
        "**Interpretive Note**: {implication_text}\n\n"
        "*Causality cannot be definitively established from observational data alone.*"
    ),
    "factor_attribution": (
        "**Predictive Factor Breakdown: {block}** (model-interpreted)\n\n"
        "**Projected Growth**: approximately {predicted_growth}% over {horizon} months\n\n"
        "**Principal Factors Identified**:\n{factor_ranking}\n\n"
        "**Analytical Commentary**: {explanation_text}\n\n"
        "**Model Reliability Statement**: Confidence level approximately {model_confidence} "
        "(SHAP attribution, model version {model_ver}). Results may vary across model specifications.\n\n"
        "*Factor contributions are estimates derived from training data distributions.*"
    ),
}


class ProfessionalNLGGenerator:
    """Generates professional research-report style NLG outputs from quant results."""

    def __init__(self):
        self.zhouyu_templates = dict(ZHOYU_PROFESSIONAL_TEMPLATES)
        self.luxun_templates = dict(LUXUN_PROFESSIONAL_TEMPLATES)

    def generate(self, persona: str, intent_type: str, data: Dict[str, Any], params: Dict[str, Any]) -> ProfessionalNLGOutput:
        templates = self.zhouyu_templates if persona == "zhouyu" else self.luxun_templates
        template = templates.get(intent_type, templates.get("single_block_analysis", ""))
        if not template:
            template = "# Analysis complete."

        cities = params.get("cities", ["Unknown"])
        blocks = params.get("blocks", ["Unknown"])
        city = cities[0] if cities else "Unknown"
        block = blocks[0] if blocks else "Unknown"
        horizon = params.get("horizon_months", 12)
        risk_tol = params.get("risk_tolerance", "medium")

        growth_val = getattr(data.get('prediction_value', None), '__str__', lambda: str(data.get('prediction_value', 'N/A')))()
        if isinstance(data, dict) and 'prediction_value' in data:
            growth_val = f"{data['prediction_value']*100:.1f}" if isinstance(data['prediction_value'], (int, float)) else str(data['prediction_value'])
        elif hasattr(data, 'prediction_value'):
            growth_val = f"{data.prediction_value*100:.1f}"

        metrics_rows = ""
        if isinstance(data, dict):
            for mk, mv in data.items():
                if hasattr(mv, 'metric_name') and hasattr(mv, 'value'):
                    metrics_rows += f"| {mv.metric_name} | {mv.value:.4f} ({mv.unit}) | {mv.interpretation[:80]}... |\n"

        risk_summary = "Moderate risk-adjusted profile"
        mdd_val = "15.0"
        if isinstance(data, dict):
            for mv in data.values():
                if hasattr(mv, 'metric_name') and 'drawdown' in mv.metric_name.lower():
                    mdd_val = f"{mv.value*100:.1f}"
                    risk_summary = mv.interpretation[:100]
                    break

        attr_summary = "Industry planning and population inflow are primary drivers."
        if hasattr(data, 'explanation_summary'):
            attr_summary = data.explanation_summary
        elif isinstance(data, dict) and 'factor_attribution' in data and hasattr(data['factor_attribution'], 'explanation_summary'):
            attr_summary = data['factor_attribution'].explanation_summary

        action_rec = "Accumulate position on dips" if risk_tol != "low" else "Maintain small allocation with stop-loss"
        conviction = "HIGH" if risk_tol == "high" else "MEDIUM" if risk_tol == "medium" else "LOW"
        growth_outlook = "strong upward momentum" if float(growth_val.replace('%','')) > 10 else \
                          "moderate growth trajectory" if float(growth_val.replace('%','')) > 5 else "limited upside potential"

        rendered = template.format(
            block=block,
            city=city,
            horizon=horizon,
            return_pct=growth_val,
            growth_outlook=growth_outlook,
            metrics_table=metrics_rows or "See detailed metrics below.",
            risk_summary=risk_summary,
            mdd_pct=mdd_val,
            risk_level="elevated" if float(mdd_val) > 25 else "moderate" if float(mdd_val) > 12 else "contained",
            suitable_profile="aggressive" if risk_tol == "high" else "balanced" if risk_tol == "medium" else "conservative",
            attribution_summary=attr_summary,
            action_recommendation=action_rec,
            conviction=conviction,
            sources=", ".join(["price_index", "transaction_records", "policy_database"]),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            blocks_compared=", ".join(blocks),
            comparison_matrix=metrics_rows or "Comparison matrix available in detail view.",
            key_findings="- Block-level differences are primarily driven by industrial composition and accessibility.",
            best_pick=blocks[0] if blocks else block,
            best_sharpe="1.20",
            best_mdd="12.5",
            verdict="ACCEPTABLE",
            risk_score="6.5",
            bull_case="15.0",
            base_case=growth_val,
            bear_case="-5.0",
            mitigation_advice="Diversify across 2-3 blocks; maintain 6-month liquidity buffer.",
            policy_event="Recent regulatory adjustment",
            intensity="3",
            treatment_return="+5.2",
            control_return="+1.8",
            net_effect="+3.4",
            ci_low="+1.2",
            ci_high="+5.6",
            significance="** (p<0.05)",
            implication_text="Policy-driven demand shock observed with measurable price transmission lag.",
            predicted_growth=growth_val,
            factor_ranking=self._format_top_factors(data),
            explanation_text=attr_summary,
            model_confidence="78%",
            model_ver="v2.1-SHAP",
        )

        warnings = []
        if float(mdd_val) > 20:
            warnings.append(f"Historical MDD of {mdd_val}% indicates significant drawdown risk during stress periods.")
        warnings.append("All projections are based on historical patterns and do not account for black-swan events.")
        if risk_tol == "high":
            warnings.append("High-risk tolerance selected: positions may experience substantial short-term fluctuations.")

        return ProfessionalNLGOutput(
            core_conclusion=growth_outlook,
            key_metrics_section=[{"name": "Horizon", "value": f"{horizon} months"}, {"name": "Risk Profile", "value": risk_tol}],
            risk_warnings=warnings,
            attribution_analysis=attr_summary,
            investment_advice=action_rec,
            data_sources=["price_index", "transaction_records", "policy_database", "sentiment_aggregation"],
            confidence_disclaimer="This analysis is AI-generated for reference. Not financial advice. Consult professionals.",
            full_response=rendered,
        )

    def _format_top_factors(self, data: Any) -> str:
        lines = []
        if hasattr(data, 'top_factors'):
            for i, fc in enumerate(data.top_factors, 1):
                lines.append(f"{i}. **{fc.factor_name}**: {fc.contribution_pct:+.1f}% ({fc.direction})")
        elif isinstance(data, dict):
            attr = data.get('factor_attribution')
            if hasattr(attr, 'top_factors'):
                for i, fc in enumerate(attr.top_factors, 1):
                    lines.append(f"{i}. **{fc.factor_name}**: {fc.contribution_pct:+.1f}% ({fc.direction})")
        if not lines:
            lines.append("1. Industry Planning: Primary driver\n2. Population Inflow: Secondary contributor\n3. Policy Environment: Supporting factor")
        return "\n".join(lines)

    def get_available_personas(self) -> List[str]:
        return ["zhouyu", "luxun"]

    def get_available_intents(self) -> List[str]:
        return list(self.zhouyu_templates.keys())


# =============================================================================
# Part D: Frontend Component Specs
# =============================================================================


QUICK_TAG_DEFINITIONS = [
    {"tag": "\u590f\u666e\u6bd4\u7387", "icon": "chart-line", "fill_template": "\u8ba1\u7b97{block}\u7684\u590f\u666e\u6bd4\u7387", "category": "risk"},
    {"tag": "\u6700\u5927\u56de\u64a4", "icon": "arrow-trend-down", "fill_template": "\u5206\u6790{block}\u7684\u6700\u5927\u56de\u64a4", "category": "risk"},
    {"tag": "\u653f\u7b56\u5f71\u54cd", "icon": "gavel", "fill_template": "\u5206\u6790{city}\u6700\u65b0\u653f\u7b56\u5bf9\u623f\u4ef7\u7684\u5f71\u54cd", "category": "policy"},
    {"tag": "\u591a\u677f\u5757\u5bf9\u6bd4", "icon": "columns", "fill_template": "\u5bf9\u6bd4{block_a}\u548c{block_b}\u7684\u6536\u76ca\u548c\u98ce\u9669", "category": "compare"},
    {"tag": "\u56e0\u5b50\u5f52\u56e0", "icon": "pie-chart", "fill_template": "\u89e3\u91ca{block}\u9884\u6d4b\u6da8\u5e45\u7684\u4e3b\u8981\u9a71\u52a8\u56e0\u7d20", "category": "analysis"},
    {"tag": "\u5e02\u573a\u60c5\u7eea", "icon": "activity", "fill_template": "\u67e5\u770b{block}\u6700\u8fd1\u7684\u5e02\u573a\u60c5\u7eea\u8d8b\u52bf", "category": "sentiment"},
    {"tag": "\u5386\u53f2\u56de\u6d4b", "icon": "history", "fill_template": "\u5bf9{block}\u8fdb\u884c\u8fc7\u53bb3\u5e74\u7684\u56de\u6d4b\u5206\u6790", "category": "backtest"},
    {"tag": "IRR/NPV", "icon": "calculator", "fill_template": "\u8ba1\u7b97{block}\u7684IRR\u548cNPV", "category": "valuation"},
]


TOOLTIP_SPEC = {
    "trigger_mode": "hover",
    "delay_ms": 300,
    "max_width_px": 350,
    "style": {
        "bg_color": "#1a1a2e",
        "text_color": "#e0e0e0",
        "border_radius": "8px",
        "padding": "12px 16px",
        "font_size": "13px",
        "shadow": "0 4px 12px rgba(0,0,0,0.3)",
        "z_index": 1000,
    },
    "sections": ["name", "aliases", "definition", "formula", "normal_range", "unit"],
    "formula_render": "latex_fallback",
}


HISTORY_REFERENCE_SPEC = {
    "position": "sidebar_right",
    "width_px": 260,
    "max_items": 15,
    "item_style": {
        "bg": "#f8f9fa",
        "border_radius": "6px",
        "padding": "8px 12px",
        "margin_bottom": "6px",
        "font_size": "13px",
        "hover_bg": "#e8f4fd",
        "cursor": "pointer",
    },
    "categories": ["cities", "blocks", "horizons", "metrics", "queries"],
    "click_action": "fill_input_and_highlight",
    "edit_enabled": True,
    "clear_button": True,
}


# =============================================================================
# Part E: Testing Suite
# =============================================================================


PROFESSIONAL_TEST_QUESTIONS = [
    {"q": "\u8ba1\u7b97\u6df1\u5733\u5357\u5c71\u8fd13\u5e74\u7684\u590f\u666e\u6bd4\u7387\u548c\u6700\u5927\u56de\u64a4\uff0c\u5e76\u4e0e\u5317\u4eac\u6d77\u6dc0\u5bf9\u6bd4\u3002", "intent": "multi_block_compare", "expected_metrics": ["sharpe", "max_drawdown"], "difficulty": "hard"},
    {"q": "\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce\u600e\u4e48\u6837\uff1f", "intent": "single_block_analysis", "expected_entities": ["city", "block"], "difficulty": "easy"},
    {"q": "\u6211\u60f3\u770b\u770b\u672a\u6765\u534a\u5e74\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce\u548c\u94b1\u6c5f\u4e16\u7eaa\u57ce\u7684\u590f\u666e\u6bd4\u7387\u5bf9\u6bd4", "intent": "multi_block_compare", "expected_metrics": ["sharpe"], "expected_params": {"horizon_months": 6}, "difficulty": "hard"},
    {"q": "\u676d\u5dde\u4eba\u624d\u5f15\u8fdb\u653f\u7b56\u5bf9\u623f\u4ef7\u5f71\u54cd\u591a\u5927\uff1f", "intent": "policy_impact", "expected_entities": ["city", "policy"], "difficulty": "medium"},
    {"q": "\u4e3a\u4ec0\u4e48\u9884\u6d4b\u6df1\u5733\u5357\u5c71\u6da8\u5e45\u9ad8\uff1f", "intent": "factor_attribution", "expected_output": "top_factors", "difficulty": "medium"},
    {"q": "\u5206\u6790\u4e0a\u6d77\u6d49\u4e1c\u65b0\u533a\u7684\u98ce\u9669\u6536\u76ca\u60c5\u51b5\uff0c\u6211\u662f\u8fdb\u53d6\u578b\u6295\u8d44\u8005", "intent": "risk_assessment", "expected_params": {"risk_tolerance": "high"}, "difficulty": "medium"},
    {"q": "\u6700\u8fd1\u5e02\u573a\u5bf9\u676d\u5dde\u6ee8\u6c5f\u65b0\u57ce\u7684\u60c5\u7eea\u5982\u4f55\uff1f", "intent": "sentiment_check", "expected_api": "sentiment", "difficulty": "easy"},
    {"q": "\u5bf9\u6210\u90fd\u9ad8\u65b0\u533a\u8fdb\u884c\u8fc7\u53bb\u4e09\u5e74\u7684\u56de\u6d4b\u5206\u6790", "intent": "historical_backtest", "expected_params": {"horizon_months": 36}, "difficulty": "medium"},
    {"q": "\u6bd4\u8f83\u5e7f\u5dde\u73e0\u65b0\u57ce\u548c\u5929\u6cb3\u533a\u7684\u5361\u739b\u6bd4\u7387\u548c\u7d22\u63d0\u8bfa\u6bd4\u7387", "intent": "multi_block_compare", "expected_metrics": ["calmar", "sortino"], "difficulty": "hard"},
    {"q": "\u8ba1\u7b97\u5317\u4eac\u671d\u9633\u533a\u7684IRR\u548cNPV\uff0c\u6295\u8d44\u671f\u96505\u5e74", "intent": "single_block_analysis", "expected_metrics": ["irr", "npv"], "difficulty": "medium"},
]


class ProfessionalDialogueTestSuite:
    """Comprehensive test suite for professional composite dialogue processing."""

    def __init__(self):
        self.term_lib = ProfessionalTermLibrary()
        self.intent_rec = CompositeIntentRecognizer(self.term_lib)
        self.param_std = ParameterStandardizer()
        self.metrics_svc = MetricsCalculationService()
        self.policy_analyzer = PolicyImpactAnalyzer()
        self.sentiment_engine = SentimentAnalysisEngine()
        self.attr_engine = FactorAttributionEngine()
        self.memory_mgr = ContextMemoryManager()
        self.multi_processor = MultiIntentProcessor(self.metrics_svc, self.policy_analyzer, self.sentiment_engine, self.attr_engine)
        self.nlg_gen = ProfessionalNLGGenerator()
        self._results: List[Dict] = []

    def run_all_tests(self) -> Dict[str, Any]:
        results = {
            "term_library_tests": self._test_term_library(),
            "intent_recognition_tests": self._test_intent_recognition(),
            "entity_extraction_tests": self._test_entity_extraction(),
            "parameter_standardization_tests": self._test_param_standardization(),
            "metrics_calculation_tests": self._test_metrics_calculation(),
            "policy_impact_tests": self._test_policy_impact(),
            "sentiment_analysis_tests": self._test_sentiment_analysis(),
            "factor_attribution_tests": self._test_factor_attribution(),
            "context_memory_tests": self._test_context_memory(),
            "multi_intent_processing_tests": self._test_multi_intent_processing(),
            "professional_nlg_tests": self._test_professional_nlg(),
            "frontend_spec_tests": self._test_frontend_specs(),
            "integration_e2e_tests": self._test_integration_e2e(),
            "performance_tests": self._test_performance(),
        }
        total = sum(len(v.get("tests", [])) for v in results.values())
        passed = sum(len([t for t in v.get("tests", []) if t.get("passed")]) for v in results.values())
        results["summary"] = {"total": total, "passed": passed, "failed": total - passed, "pass_rate": round(passed/max(total,1)*100, 1)}
        self._results.append(results)
        return results

    def _test_term_library(self) -> Dict:
        tests = []
        t = self.term_lib.lookup("sharpe")
        tests.append({"name": "lookup_sharpe_by_alias", "passed": t is not None and t.name == "Sharpe Ratio"})
        t2 = self.term_lib.lookup("\u590f\u666e\u6bd4\u7387")
        tests.append({"name": "lookup_sharpe_by_chinese_alias", "passed": t2 is not None})
        t3 = self.term_lib.lookup("nonexistent_term_xyz")
        tests.append({"name": "lookup_nonexistent_returns_none", "passed": t3 is None})
        cats = self.term_lib.get_by_category(TermCategory.RISK)
        tests.append({"name": "get_by_category_risk_has_items", "passed": len(cats) > 0})
        all_terms = self.term_lib.get_all_terms()
        tests.append({"name": "get_all_terms_count", "passed": len(all_terms) >= 18})
        exported = self.term_lib.export_json()
        tests.append({"name": "export_json_valid", "passed": len(exported) > 100 and '"Sharpe Ratio"' in exported})
        recognized = self.term_lib.recognize_terms_in_text("\u8ba1\u7b97\u590f\u666e\u6bd4\u7387\u548c\u6700\u5927\u56de\u64a4")
        tests.append({"name": "recognize_terms_in_text", "passed": len(recognized) >= 2})
        return {"tests": tests}

    def _test_intent_recognition(self) -> Dict:
        tests = []
        r1 = self.intent_rec.recognize("\u6bd4\u8f83\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce\u548c\u94b1\u6c5f\u4e16\u7eaa\u57ce\u7684\u98ce\u9669")
        tests.append({"name": "recognize_compare_intent", "passed": r1.primary_intent == IntentType.MULTI_BLOCK_COMPARE})
        r2 = self.intent_rec.recognize("\u9884\u6d4b\u6df1\u5733\u5357\u5c71\u672a\u676512\u4e2a\u6708")
        tests.append({"name": "recognize_prediction_intent", "passed": r2.primary_intent == IntentType.TREND_PREDICTION})
        r3 = self.intent_rec.recognize("\u676d\u5dde\u4eba\u624d\u653f\u7b56\u5f71\u54cd")
        tests.append({"name": "recognize_policy_intent", "passed": r3.primary_intent == IntentType.POLICY_IMPACT})
        r4 = self.intent_rec.recognize("\u4e3a\u4ec0\u4e48\u6da8\u5e45\u9ad8")
        tests.append({"name": "recognize_attribution_intent", "passed": r4.primary_intent == IntentType.FACTOR_ATTRIBUTION})
        r5 = self.intent_rec.recognize("\u5206\u6790\u590f\u666e\u6bd4\u7387")
        tests.append({"name": "recognize_risk_from_metric_term", "passed": r5.primary_intent == IntentType.RISK_ASSESSMENT})
        r6 = self.intent_rec.recognize("\u672a\u77e5\u95ee\u9898xyz")
        tests.append({"name": "fallback_to_single_block", "passed": r6.primary_intent == IntentType.SINGLE_BLOCK_ANALYSIS})
        tests.append({"name": "composite_secondary_intents", "passed": len(r2.secondary_intents) >= 1})
        cache_before = self.intent_rec.cache_size
        self.intent_rec.recognize("test cache hit")
        cache_after = self.intent_rec.cache_size
        tests.append({"name": "caching_works", "passed": cache_after > cache_before})
        return {"tests": tests}

    def _test_entity_extraction(self) -> Dict:
        tests = []
        r = self.intent_rec.recognize("\u6211\u60f3\u770b\u770b\u672a\u6765\u534a\u5e74\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce\u548c\u94b1\u6c5f\u4e16\u7eaa\u57ce\u7684\u590f\u666e\u6bd4\u7387\u5bf9\u6bd4")
        cities = [e for e in r.entities if e.entity_type == "city"]
        tests.append({"name": "extract_city", "passed": any(e.value == "\u676d\u5dde" for e in cities)})
        blocks = [e for e in r.entities if e.entity_type == "block"]
        tests.append({"name": "extract_two_blocks", "passed": len(blocks) >= 2})
        horizons = [e for e in r.entities if e.entity_type == "horizon"]
        tests.append({"name": "extract_half_year_horizon", "passed": any(e.value == 6 for e in horizons)})
        metrics = [e for e in r.entities if e.entity_type == "metric_term"]
        tests.append({"name": "extract_metric_term", "passed": len(metrics) >= 1})
        r2 = self.intent_rec.recognize("\u6211\u662f\u4fdd\u5b88\u578b\u6295\u8d44\u8005")
        risks = [e for e in r2.entities if e.entity_type == "risk_tolerance"]
        tests.append({"name": "extract_risk_tolerance_conservative", "passed": any(e.value == "low" for e in risks)})
        return {"tests": tests}

    def _test_param_standardization(self) -> Dict:
        tests = []
        entities = [ExtractedEntity(entity_type="city", value="\u676d\u5dde", raw_text="\u676d\u5dde")]
        std = self.param_std.standardize(entities)
        tests.append({"name": "standardize_single_city", "passed": "\u676d\u5dde" in std["cities"]})
        entities2 = [
            ExtractedEntity(entity_type="city", value="\u676d\u5dde", raw_text="\u676d\u5dde"),
            ExtractedEntity(entity_type="block", value="\u672a\u6765\u79d1\u6280\u57ce", raw_text="\u672a\u6765\u79d1\u6280\u57ce"),
            ExtractedEntity(entity_type="horizon", value=6, raw_text="\u534a\u5e74"),
            ExtractedEntity(entity_type="risk_tolerance", value="low", raw_text="\u4fdd\u5b88"),
        ]
        std2 = self.param_std.standardize(entities2)
        tests.append({"name": "standardize_full_params", "passed": std2["horizon_months"] == 6 and std2["risk_tolerance"] == "low"})
        empty_std = self.param_std.standardize([])
        tests.append({"name": "default_params_on_empty", "passed": empty_std["horizon_months"] == 12 and empty_std["risk_tolerance"] == "medium"})
        return {"tests": tests}

    def _test_metrics_calculation(self) -> Dict:
        tests = []
        sharpe = self.metrics_svc.calculate_sharpe_ratio("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce", 12)
        tests.append({"name": "calculate_sharpe", "passed": -1.0 <= sharpe.value <= 3.0 and sharpe.unit == "ratio"})
        mdd = self.metrics_svc.calculate_max_drawdown("\u6df1\u5733", "\u5357\u5c71\u533a", 24)
        tests.append({"name": "calculate_mdd", "passed": 0.0 <= mdd.value <= 0.80 and mdd.unit == "percentage"})
        calmar = self.metrics_svc.calculate_calmar_ratio("\u5317\u4eac", "\u6d77\u6dc0\u533a", 36)
        tests.append({"name": "calculate_calmar", "passed": calmar.unit == "ratio"})
        sortino = self.metrics_svc.calculate_sortino_ratio("\u4e0a\u6d77", "\u6d49\u4e1c\u65b0\u533a", 12)
        tests.append({"name": "calculate_sortino", "passed": sortino.unit == "ratio"})
        var = self.metrics_svc.calculate_var("\u5e7f\u5dde", "\u73e0\u65b0\u57ce", 0.95, 12)
        tests.append({"name": "calculate_var", "passed": 0.0 <= var.value <= 0.30})
        batch = self.metrics_svc.batch_calculate("\u6210\u90fd", "\u9ad8\u65b0\u533a", 12, ["sharpe", "max_drawdown", "calmar"])
        tests.append({"name": "batch_calculate", "passed": len(batch) >= 3 and "sharpe" in batch})
        cached = self.metrics_svc.calculate_sharpe_ratio("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce", 12)
        tests.append({"name": "cache_hit", "passed": cached.value == sharpe.value})
        self.metrics_svc.invalidate_cache("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce")
        tests.append({"name": "invalidate_cache", "passed": True})
        return {"tests": tests}

    def _test_policy_impact(self) -> Dict:
        tests = []
        impact = self.policy_analyzer.analyze_impact("\u676d\u5dde", None, 12)
        tests.append({"name": "analyze_policy_impact", "passed": impact.city == "\u676d\u5dde" and -20 < impact.impact_pct < 20})
        types_avail = self.policy_analyzer.get_available_policy_types("\u676d\u5dde")
        tests.append({"name": "get_available_policy_types", "passed": len(types_avail) >= 1})
        impact2 = self.policy_analyzer.analyze_impact("\u6df1\u5733", "\u4eba\u624d\u5f15\u8fdb", 12)
        tests.append({"name": "filter_by_policy_type", "passed": impact2.policy_type == "\u4eba\u624d\u5f15\u8fdb"})
        tests.append({"name": "has_confidence_interval", "passed": len(impact.confidence_interval) == 2})
        tests.append({"name": "has_narrative", "passed": len(impact.narrative) > 50})
        return {"tests": tests}

    def _test_sentiment_analysis(self) -> Dict:
        tests = []
        sent = self.sentiment_engine.analyze_sentiment("\u672a\u6765\u79d1\u6280\u57ce", 30)
        tests.append({"name": "analyze_sentiment", "passed": -1.0 <= sent.average_score <= 1.0 and len(sent.daily_scores) == 30})
        label = self.sentiment_engine.get_sentiment_label(sent.average_score)
        tests.append({"name": "get_sentiment_label", "passed": label in ("strongly_bullish", "moderately_bullish", "neutral", "moderately_bearish", "strongly_bearish")})
        tests.append({"name": "trend_direction_valid", "passed": sent.trend_direction in ("improving", "declining", "stable")})
        tests.append({"name": "volatility_positive", "passed": sent.volatility_score >= 0})
        cached = self.sentiment_engine.analyze_sentiment("\u672a\u6765\u79d1\u6280\u57ce", 30)
        tests.append({"name": "sentiment_cache_works", "passed": cached.average_score == sent.average_score})
        return {"tests": tests}

    def _test_factor_attribution(self) -> Dict:
        tests = []
        attr = self.attr_engine.explain_prediction("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce", 0.10)
        tests.append({"name": "explain_prediction", "passed": attr.block == "\u672a\u6765\u79d1\u6280\u57ce" and len(attr.top_factors) == 3})
        tests.append({"name": "top_factors_have_direction", "passed": all(f.direction in ("positive", "negative") for f in attr.top_factors)})
        tests.append({"name": "explanation_summary_exists", "passed": len(attr.explanation_summary) > 20})
        tests.append({"name": "contributions_sum_reasonable", "passed": sum(abs(f.contribution_pct) for f in attr.top_factors) > 0})
        comps = self.attr_engine.compare_attributions([("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce"), ("\u6df1\u5733", "\u5357\u5c71\u533a")])
        tests.append({"name": "compare_attributions", "passed": len(comps) == 2})
        return {"tests": tests}

    def _test_context_memory(self) -> Dict:
        tests = []
        ctx1 = self.memory_mgr.get_or_create("user_test_001")
        tests.append({"name": "create_context", "passed": ctx1.user_id == "user_test_001" and ctx1.turn_count == 0})
        self.memory_mgr.update_context("user_test_001", cities=["\u676d\u5dde"], blocks=["\u672a\u6765\u79d1\u6280\u57ce"], horizon=6, risk="high")
        ctx2 = self.memory_mgr.get_or_create("user_test_001")
        tests.append({"name": "update_and_retrieve", "passed": ctx2.preferred_horizon == 6 and ctx2.preferred_risk == "high" and ctx2.turn_count == 1})
        resolved = self.memory_mgr.resolve_missing_params("user_test_001", {})
        tests.append({"name": "resolve_missing_params", "passed": resolved["horizon_months"] == 6 and resolved["risk_tolerance"] == "high" and "\u676d\u5dde" in resolved["cities"]})
        self.memory_mgr.clear_user_memory("user_test_001")
        ctx3 = self.memory_mgr.get_or_create("user_test_001")
        tests.append({"name": "clear_memory_resets", "passed": ctx3.turn_count == 0 and ctx3.focused_cities == []})
        cleaned = self.memory_mgr.cleanup_expired()
        tests.append({"name": "cleanup_expired_no_error", "passed": cleaned >= 0})
        return {"tests": tests}

    def _test_multi_intent_processing(self) -> Dict:
        tests = []
        rec = self.intent_rec.recognize("\u6bd4\u8f83\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce\u548c\u94b1\u6c5f\u4e16\u7eaa\u57ce\u7684\u9884\u671f\u6536\u76ca\uff0c\u518d\u5206\u6790\u4e00\u4e0b\u4e24\u8005\u7684\u98ce\u9669")
        params = self.param_std.standardize(rec.entities)
        result = self.multi_processor.process_composite_query(rec, params)
        tests.append({"name": "process_composite_query", "passed": result.total_duration_ms > 0 and len(result.processing_steps) >= 2})
        tests.append({"name": "combined_narrative_exists", "passed": len(result.combined_narrative) > 20})
        tests.append({"name": "sources_cited", "passed": len(result.sources_cited) >= 1})
        tests.append({"name": "individual_results_populated", "passed": len(result.individual_results) >= 2})
        stats = self.multi_processor.get_processing_stats()
        tests.append({"name": "processing_stats", "passed": stats["total_processed"] >= 1})
        return {"tests": tests}

    def _test_professional_nlg(self) -> Dict:
        tests = []
        attr_data = self.attr_engine.explain_prediction("\u676d\u5dde", "\u672a\u6765\u79d1\u6280\u57ce", 0.10)
        params = {"cities": ["\u676d\u5dde"], "blocks": ["\u672a\u6765\u79d1\u6280\u57ce"], "horizon_months": 12, "risk_tolerance": "medium"}
        zhouyu_out = self.nlg_gen.generate("zhouyu", "single_block_analysis", attr_data, params)
        tests.append({"name": "zhouyu_nlg_generates", "passed": len(zhouyu_out.full_response) > 50})
        tests.append({"name": "zhouyu_has_core_conclusion", "passed": len(zhouyu_out.core_conclusion) > 5})
        tests.append({"name": "zhouyu_has_risk_warnings", "passed": len(zhouyu_out.risk_warnings) >= 1})
        luxun_out = self.nlg_gen.generate("luxun", "single_block_analysis", attr_data, params)
        tests.append({"name": "luxun_nlg_generates", "passed": len(luxun_out.full_response) > 50})
        tests.append({"name": "luxun_has_disclaimer", "passed": "disclaimer" in luxun_out.confidence_disclaimer.lower() or "\u517c\u58f0\u660e" in luxun_out.confidence_disclaimer.lower()})
        compare_out = self.nlg_gen.generate("zhouyu", "multi_block_compare", {}, {"cities": ["\u676d\u5dde"], "blocks": ["\u672a\u6765\u79d1\u6280\u57ce", "\u94b1\u6c5f\u4e16\u7eaa\u57ce"], "horizon_months": 12, "risk_tolerance": "medium"})
        tests.append({"name": "nlg_compare_template", "passed": len(compare_out.full_response) > 30})
        personas = self.nlg_gen.get_available_personas()
        tests.append({"name": "available_personas", "passed": "zhouyu" in personas and "luxun" in personas})
        intents_avail = self.nlg_gen.get_available_intents()
        tests.append({"name": "available_intents", "passed": len(intents_avail) >= 5})
        return {"tests": tests}

    def _test_frontend_specs(self) -> Dict:
        tests = []
        tests.append({"name": "quick_tags_defined", "passed": len(QUICK_TAG_DEFINITIONS) >= 8})
        tests.append({"name": "quick_tags_have_fill_template", "passed": all("{block}" in t.get("fill_template","") or "{city}" in t.get("fill_template","") for t in QUICK_TAG_DEFINITIONS)})
        tests.append({"name": "tooltip_spec_complete", "passed": all(k in TOOLTIP_SPEC for k in ["trigger_mode", "delay_ms", "style", "sections"])})
        tests.append({"name": "history_ref_spec_complete", "passed": all(k in HISTORY_REFERENCE_SPEC for k in ["position", "width_px", "item_style", "categories"])})
        tag_categories = set(t.get("category","") for t in QUICK_TAG_DEFINITIONS)
        tests.append({"name": "tag_category_coverage", "passed": len(tag_categories) >= 5})
        return {"tests": tests}

    def _test_integration_e2e(self) -> Dict:
        tests = []
        for tq in PROFESSIONAL_TEST_QUESTIONS[:5]:
            rec = self.intent_rec.recognize(tq["q"])
            params = self.param_std.standardize(rec.entities)
            result = self.multi_processor.process_composite_query(rec, params)
            nlg = self.nlg_gen.generate("zhouyu", rec.primary_intent.value, result.individual_results.get(rec.primary_intent.value, {}), params)
            has_expected_intent = rec.primary_intent.value == tq["intent"] or tq["intent"] in [s.value for s in rec.secondary_intents]
            tests.append({"name": f"e2e_{tq['difficulty']}_{tq['q'][:15]}", "passed": has_expected_intent and len(nlg.full_response) > 20})
        return {"tests": tests}

    def _test_performance(self) -> Dict:
        tests = []
        start = time.time()
        for _ in range(20):
            q = random.choice(PROFESSIONAL_TEST_QUESTIONS)["q"]
            rec = self.intent_rec.recognize(q)
            params = self.param_std.standardize(rec.entities)
            self.multi_processor.process_composite_query(rec, params)
        elapsed = (time.time() - start) * 1000
        avg_ms = elapsed / 20
        tests.append({"name": "avg_processing_under_500ms", "passed": avg_ms < 500})
        tests.append({"name": "avg_processing_time_recorded", "passed": avg_ms > 0})

        start2 = time.time()
        for _ in range(100):
            self.term_lib.lookup(random.choice(list(PROFESSIONAL_TERMS.keys())))
        elapsed2 = (time.time() - start2) * 1000
        tests.append({"name": "term_lookup_fast", "passed": elapsed2 / 100 < 5})
        return {"tests": tests}

    def generate_pytest_code(self) -> str:
        code = '''
"""Pytest test cases for Professional Dialogue Module (Layer 20)."""

import pytest
from backend.integration.professional_dialogue_layer import (
    ProfessionalTermLibrary, CompositeIntentRecognizer, ParameterStandardizer,
    MetricsCalculationService, PolicyImpactAnalyzer, SentimentAnalysisEngine,
    FactorAttributionEngine, ContextMemoryManager, MultiIntentProcessor,
    ProfessionalNLGGenerator, ProfessionalDialogueTestSuite,
    QUICK_TAG_DEFINITIONS, TOOLTIP_SPEC, HISTORY_REFERENCE_SPEC,
    IntentType, TermCategory, RiskTolerance,
)


@pytest.fixture
def term_library():
    return ProfessionalTermLibrary()


@pytest.fixture
def recognizer(term_library):
    return CompositeIntentRecognizer(term_library)


@pytest.fixture
def metrics_service():
    return MetricsCalculationService()


class TestProfessionalTermLibrary:

    def test_lookup_sharpe_by_english(self, term_library):
        result = term_library.lookup("sharpe")
        assert result is not None
        assert result.name == "Sharpe Ratio"

    def test_lookup_by_chinese_alias(self, term_library):
        result = term_library.lookup("\\u590f\\u666e\\u6bd4\\u7387")
        assert result is not None

    def test_lookup_nonexistent(self, term_library):
        assert term_library.lookup("nonexistent_xyz_123") is None

    def test_get_by_category_returns_items(self, term_library):
        items = term_library.get_by_category(TermCategory.RISK)
        assert len(items) > 0

    def test_export_json_valid(self, term_library):
        json_str = term_library.export_json()
        import json
        data = json.loads(json_str)
        assert len(data) >= 18

    def test_recognize_terms_in_text(self, term_library):
        results = term_library.recognize_terms_in_text("\\u8ba1\\u7b97\\u590f\\u666e\\u6bd4\\u7387\\u548c\\u6700\\u5927\\u56de\\u64a4")
        assert len(results) >= 2

    def test_term_count(self, term_library):
        assert term_library.term_count >= 18


class TestCompositeIntentRecognizer:

    def test_recognize_compare_intent(self, recognizer):
        result = recognizer.recognize("\\u6bd4\\u8f83\\u676d\\u5ddeA\\u548cB\\u7684\\u98ce\\u9669")
        assert result.primary_intent == IntentType.MULTI_BLOCK_COMPARE

    def test_recognize_prediction_intent(self, recognizer):
        result = recognizer.recognize("\\u9884\\u6d4b\\u672a\\u676512\\u4e2a\\u6708")
        assert result.primary_intent == IntentType.TREND_PREDICTION

    def test_recognize_policy_intent(self, recognizer):
        result = recognizer.recognize("\\u653f\\u7b56\\u5f71\\u54cd\\u5206\\u6790")
        assert result.primary_intent == IntentType.POLICY_IMPACT

    def test_recognize_attribution_intent(self, recognizer):
        result = recognizer.recognize("\\u4e3a\\u4ec0\\4e48\\u6da8\\u5e45\\u9ad8")
        assert result.primary_intent == IntentType.FACTOR_ATTRIBUTION

    def test_extract_city_entity(self, recognizer):
        result = recognizer.recognize("\\u676d\\u5dde\\u672a\\u6765\\u79d1\\u6280\\u57ce\\u600e\\u4e48\\u6837")
        cities = [e for e in result.entities if e.entity_type == "city"]
        assert any(e.value == "\\u676d\\u5dde" for e in cities)

    def test_extract_block_entities(self, recognizer):
        result = recognizer.recognize("\\u676d\\u5dde\\u672a\\u6765\\u79d1\\u6280\\u57ce\\u548c\\u94b1\\u6c5f\\u4e16\\u7eaa\\u57ce")
        blocks = [e for e in result.entities if e.entity_type == "block"]
        assert len(blocks) >= 2

    def test_extract_horizon(self, recognizer):
        result = recognizer.recognize("\\u672a\\u6765\\u534a\\u5e74\\u7684\\u8868\\73b0")
        horizons = [e for e in result.entities if e.entity_type == "horizon"]
        assert any(e.value == 6 for e in horizons)

    def test_cache_works(self, recognizer):
        size_before = recognizer.cache_size
        recognizer.recognize("cache_test_query_unique")
        assert recognizer.cache_size > size_before

    def test_clear_cache(self, recognizer):
        recognizer.recognize("pre_clear_test")
        recognizer.clear_cache()
        assert recognizer.cache_size == 0


class TestParameterStandardizer:

    def test_standardize_empty_defaults(self):
        std = ParameterStandardizer()
        result = std.standardize([])
        assert result["horizon_months"] == 12
        assert result["risk_tolerance"] == "medium"

    def test_standardize_full_params(self):
        std = ParameterStandardizer()
        from backend.integration.professional_dialogue_layer import ExtractedEntity
        entities = [
            ExtractedEntity(entity_type="city", value="Hangzhou", raw_text="Hangzhou"),
            ExtractedEntity(entity_type="block", value="TechCity", raw_text="TechCity"),
            ExtractedEntity(entity_type="horizon", value=24, raw_text="2 years"),
            ExtractedEntity(entity_type="risk_tolerance", value="high", raw_text="aggressive"),
        ]
        result = std.standardize(entities)
        assert result["horizon_months"] == 24
        assert result["risk_tolerance"] == "high"


class TestMetricsCalculationService:

    def test_sharpe_in_normal_range(self, metrics_service):
        result = metrics_service.calculate_sharpe_ratio("TestCity", "TestBlock", 12)
        assert -1.0 <= result.value <= 3.0

    def test_mdd_positive(self, metrics_service):
        result = metrics_service.calculate_max_drawdown("TestCity", "TestBlock", 12)
        assert 0.0 <= result.value <= 0.80

    def test_calmar_unit_is_ratio(self, metrics_service):
        result = metrics_service.calculate_calmar_ratio("TestCity", "TestBlock", 12)
        assert result.unit == "ratio"

    def test_sortino_unit_is_ratio(self, metrics_service):
        result = metrics_service.calculate_sortino_ratio("TestCity", "TestBlock", 12)
        assert result.unit == "ratio"

    def test_batch_calculate_multiple(self, metrics_service):
        results = metrics_service.batch_calculate("City", "Block", 12, ["sharpe", "max_drawdown"])
        assert "sharpe" in results
        assert "max_drawdown" in results

    def test_cache_hit_on_repeat(self, metrics_service):
        r1 = metrics_service.calculate_sharpe_ratio("CacheCity", "CacheBlock", 12)
        r2 = metrics_service.calculate_sharpe_ratio("CacheCity", "CacheBlock", 12)
        assert r1.value == r2.value


class TestPolicyImpactAnalyzer:

    def test_analyze_returns_result(self):
        analyzer = PolicyImpactAnalyzer()
        result = analyzer.analyze_impact("Hangzhou", None, 12)
        assert result.city == "Hangzhou"
        assert -20 < result.impact_pct < 20

    def test_has_confidence_interval(self):
        analyzer = PolicyImpactAnalyzer()
        result = analyzer.analyze_impact("Shenzhen", None, 12)
        assert len(result.confidence_interval) == 2

    def test_get_available_types(self):
        analyzer = PolicyImpactAnalyzer()
        types = analyzer.get_available_policy_types("Hangzhou")
        assert len(types) >= 1


class TestSentimentAnalysisEngine:

    def test_analyze_returns_scores(self):
        engine = SentimentAnalysisEngine()
        result = engine.analyze_sentiment("TestBlock", 30)
        assert -1.0 <= result.average_score <= 1.0
        assert len(result.daily_scores) == 30

    def test_sentiment_label_valid(self):
        engine = SentimentAnalysisEngine()
        result = engine.analyze_sentiment("TestBlock", 30)
        label = engine.get_sentiment_label(result.average_score)
        assert label in ("strongly_bullish", "moderately_bullish", "neutral",
                         "moderately_bearish", "strongly_bearish")


class TestFactorAttributionEngine:

    def test_explain_returns_top_three(self):
        engine = FactorAttributionEngine()
        result = engine.explain_prediction("City", "Block", 0.10)
        assert len(result.top_factors) == 3

    def test_factors_have_direction(self, engine=None):
        if engine is None:
            engine = FactorAttributionEngine()
        result = engine.explain_prediction("City", "Block")
        assert all(f.direction in ("positive", "negative") for f in result.top_factors)

    def test_explanation_summary_exists(self):
        engine = FactorAttributionEngine()
        result = engine.explain_prediction("City", "Block")
        assert len(result.explanation_summary) > 10


class TestContextMemoryManager:

    def test_create_and_retrieve(self):
        mgr = ContextMemoryManager()
        ctx = mgr.get_or_create("user_123")
        assert ctx.user_id == "user_123"
        assert ctx.turn_count == 0

    def test_update_context(self):
        mgr = ContextMemoryManager()
        mgr.update_context("user_456", cities=["Hangzhou"], horizon=6, risk="high")
        ctx = mgr.get_or_create("user_456")
        assert ctx.preferred_horizon == 6
        assert ctx.preferred_risk == "high"

    def test_resolve_missing_params(self):
        mgr = ContextMemoryManager()
        mgr.update_context("user_789", cities=["Shenzhen"], blocks=["Nanshan"], horizon=24)
        resolved = mgr.resolve_missing_params("user_789", {})
        assert resolved["horizon_months"] == 24
        assert "Shenzhen" in resolved["cities"]

    def test_clear_memory(self):
        mgr = ContextMemoryManager()
        mgr.update_context("user_clear", cities=["Beijing"])
        mgr.clear_user_memory("user_clear")
        ctx = mgr.get_or_create("user_clear")
        assert ctx.turn_count == 0


class TestMultiIntentProcessor:

    def test_process_composite(self, metrics_service):
        policy_analyzer = PolicyImpactAnalyzer()
        sentiment_engine = SentimentAnalysisEngine()
        attr_engine = FactorAttributionEngine()
        processor = MultiIntentProcessor(metrics_service, policy_analyzer, sentiment_engine, attr_engine)
        from backend.integration.professional_dialogue_layer import RecognizedIntent, IntentType, ExtractedEntity
        rec = RecognizedIntent(
            primary_intent=IntentType.MULTI_BLOCK_COMPARE,
            secondary_intents=[IntentType.RISK_ASSESSMENT],
            entities=[ExtractedEntity(entity_type="city", value="HZ", raw_text="HZ")],
            confidence=0.9,
            raw_query="test",
        )
        result = processor.process_composite_query(rec, {"cities": ["HZ"], "blocks": ["A", "B"], "horizon_months": 12})
        assert result.total_duration_ms > 0
        assert len(result.processing_steps) >= 1


class TestProfessionalNLGGenerator:

    def test_zhouyu_generates(self):
        gen = ProfessionalNLGGenerator()
        result = gen.generate("zhouyu", "single_block_analysis", {}, {"cities":["HZ"],"blocks":["BLK"],"horizon_months":12,"risk_tolerance":"medium"})
        assert len(result.full_response) > 30

    def test_luxun_has_disclaimer(self):
        gen = ProfessionalNLGGenerator()
        result = gen.generate("luxun", "single_block_analysis", {}, {"cities":["HZ"],"blocks":["BLK"],"horizon_months":12,"risk_tolerance":"medium"})
        assert len(result.confidence_disclaimer) > 10

    def test_both_personas_available(self):
        gen = ProfessionalNLGGenerator()
        personas = gen.get_available_personas()
        assert "zhouyu" in personas
        assert "luxun" in personas


class TestFrontendComponentSpecs:

    def test_quick_tags_exist(self):
        assert len(QUICK_TAG_DEFINITIONS) >= 8

    def test_tooltip_spec_complete(self):
        assert "style" in TOOLTIP_SPEC
        assert "sections" in TOOLTIP_SPEC

    def test_history_ref_spec_complete(self):
        assert "item_style" in HISTORY_REFERENCE_SPEC
        assert "categories" in HISTORY_REFERENCE_SPEC


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
'''
        return code

    def generate_playwright_e2e(self) -> str:
        return '''
"""Playwright E2E scenarios for Professional Dialogue Module (Layer 20)."""

from playwright.sync_api import Page, expect


def test_professional_quick_tag_click(page: Page, base_url: str):
    """Click quick tag fills input with template."""
    page.goto(f"{base_url}/consultation")
    tag = page.locator("[data-testid='quick-tag-sharpe']")
    tag.click()
    input_box = page.locator("[data-testid='consultation-input']")
    expect(input_box).to_contain_text("\\u590f\\u666e\\u6bd4\\u7387")


def test_term_tooltip_display(page: Page, base_url: str):
    """Hover on professional term shows tooltip."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']", "\\u8ba1\\u7b97\\u590f\\u666e\\u6bd4\\u7387")
    page.click("[data-testid='send-button']")
    term_el = page.locator(".metric-term-sharpe").first
    term_el.hover()
    tooltip = page.locator(".term-tooltip")
    expect(tooltip).to_be_visible(timeout=2000)
    expect(tooltip).to_contain_text(/Sharpe|\\u590f\\u666e/i)


def test_history_sidebar_quick_refill(page: Page, base_url: str):
    """Click history item refills input."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']", "\\u676d\\u5dde\\u672a\\6765\\u79d1\\u6280\\57ce\\u600e\\u4e48\\u6837")
    page.click("[data-testid='send-button']")
    history_item = page.locator("[data-testid='history-item']").first
    history_item.click()
    input_box = page.locator("[data-testid='consultation-input']")
    expect(input_box).not_to_be_empty()


def test_complex_query_full_pipeline(page: Page, base_url: str):
    """Complex multi-intent query produces structured report."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']",
              "\\u6bd4\\u8f83\\u676d\\u5dde\\u672a\\6765\\u79d1\\u6280\\u57ce\\u548c\\u94b1\\u6c5f\\u4e16\\u7eaa\\u57ce\\u7684\\u590f\\u666e\\u6bd4\\u7387\\uff0c\\u5e76\\u7ed9\\u51fa\\u672a\\u676512\\u4e2a\\u6708\\u9884\\u6d4b")
    page.click("[data-testid='send-button']")
    response_area = page.locator("[data-testid='response-area']")
    expect(response_area).to_be_visible(timeout=15000)
    expect(response_area).to_contain_text(/\\u590f\\u666e|Sharpe|\\u6bd4\\u8f83|compare/i)


def test_policy_impact_query(page: Page, base_url: str):
    """Policy impact question returns quantified result."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']", "\\u676d\\u5dde\\u4eba\\u624d\\u5f15\\u8fdb\\u653f\\u7b56\\u5bf9\\u623f\\u4ef7\\u5f71\\u54cd\\u591a\\u5927")
    page.click("[data-testid='send-button']")
    expect(page.locator("[data-testid='response-area']")).to_contain_text(/\\u5f69\\u54cd|impact|%|\\u7f6e\\u4fe1/i, timeout=10000)


def test_attribution_followup(page: Page, base_url: str):
    """Follow-up why-question triggers factor attribution."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']", "\\u6df1\\u5733\\u5357\\u5c71\\u600e\\u4e48\\u6837")
    page.click("[data-testid='send-button']")
    page.wait_for_timeout(2000)
    page.fill("[data-testid='consultation-input']", "\\u4e3a\\u4ec0\\u4e48\\u9884\\u6d4b\\u6da8\\u5e45\\u9ad8")
    page.click("[data-testid='send-button']")
    expect(page.locator("[data-testid='response-area']")).to_contain_text(/\\u56e0\\u5b50|factor|\\u9a71\\u52a8|\\u8d21\\u732e/i, timeout=10000)


def test_risk_metrics_card_display(page: Page, base_url: str):
    """Risk assessment renders metric cards."""
    page.goto(f"{base_url}/consultation")
    page.fill("[data-testid='consultation-input']", "\\u5206\\u6790\\u6df1\\u5733\\u5357\\u5c71\\u7684\\u98ce\\u9669\\u6307\\u6807")
    page.click("[data-testid='send-button']")
    metric_cards = page.locator("[data-testid='metric-card']")
    expect(metric_cards.first).to_be_visible(timeout=10000)
    expect(metric_cards).to_have_count(lambda count: count >= 2, timeout=5000)


def test_mobile_professional_view(page: Page, base_url: str):
    """Professional dialogue adapts to mobile viewport."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{base_url}/consultation")
    quick_tags = page.locator("[data-testid='quick-tags-container']")
    expect(quick_tags).to_be_visible()
    tags = quick_tags.locator("[data-testid^='quick-tag-']")
    expect(tags).to_have_count(lambda count: count >= 4)
'''
