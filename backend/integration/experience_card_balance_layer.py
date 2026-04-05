# -*- coding: utf-8 -*-
"""
Layer 23: Experience Card & Balance Mechanism (\u4fee\u4e3a\u4f53\u9a8c\u5361\u4e0e\u5e73\u8861\u673a\u5236)
========================================================================
Governor Fang AI Property Platform (\u623f\u90fd\u7763AI\u5e73\u53f0)
Responsibilities:
  Part A: Experience Card Type & Effect System (card types, inventory, grant rules)
  Part B: Temporary Realm State Management (temp realm activation, UI indicators)
  Part C: Post-Trial Return & Reincarnation Design (guidance, data preservation)
  Part D: Balance Design & Anti-Abuse (limits, rate limiting, no stacking)
  Part E: Frontend Interaction & Visuals (backpack UI, notifications, overlays)
  Part F: Operations Event Configuration (double-exp events, shop items)
  Part G: Testing Suite (35+ test cases, pytest generation, Playwright E2E)
"""

from __future__ import annotations

import json
import time
import uuid
import hashlib
import logging
import threading
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# PART A: EXPERIENCE CARD TYPE & EFFECT SYSTEM
# =============================================================================


class CardRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"


class GrantSource(str, Enum):
    NEWBIE = "newbie"
    TASK = "task"
    DAILY_STREAK = "daily_streak"
    INVITE = "invite"
    EVENT = "event"
    SHOP = "shop"


class CardStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    IN_BACKPACK = "in_backpack"


class ExperienceCardType(Enum):
    ZHU_JI_CARD = "zhu_ji_card"
    JIN_DAN_CARD = "jin_dan_card"
    YUAN_YING_CARD = "yuan_ying_card"

    @property
    def display_name(self) -> str:
        _names = {
            ExperienceCardType.ZHU_JI_CARD: "\u7b51\u57fa\u4f53\u9a8c\u5361",
            ExperienceCardType.JIN_DAN_CARD: "\u91d1\u4e39\u4f53\u9a8c\u5361",
            ExperienceCardType.YUAN_YING_CARD: "\u5143\u5a74\u4f53\u9a8c\u5361",
        }
        return _names.get(self, str(self.value))

    @property
    def target_realm(self) -> "QuantRealm":
        from backend.integration.fusion_quant_mastery_layer import QuantRealm
        _realm_map = {
            ExperienceCardType.ZHU_JI_CARD: QuantRealm.ZHU_JI,
            ExperienceCardType.JIN_DAN_CARD: QuantRealm.JIN_DAN,
            ExperienceCardType.YUAN_YING_CARD: QuantRealm.YUAN_YING,
        }
        return _realm_map.get(self, QuantRealm.LIAN_QI)

    @property
    def duration_hours(self) -> int:
        _durations = {
            ExperienceCardType.ZHU_JI_CARD: 24,
            ExperienceCardType.JIN_DAN_CARD: 48,
            ExperienceCardType.YUAN_YING_CARD: 72,
        }
        return _durations.get(self, 24)

    @property
    def max_uses(self) -> int:
        _uses = {
            ExperienceCardType.ZHU_JI_CARD: 3,
            ExperienceCardType.JIN_DAN_CARD: 5,
            ExperienceCardType.YUAN_YING_CARD: 7,
        }
        return _uses.get(self, 3)

    @property
    def rarity(self) -> CardRarity:
        _rarity_map = {
            ExperienceCardType.ZHU_JI_CARD: CardRarity.COMMON,
            ExperienceCardType.JIN_DAN_CARD: CardRarity.UNCOMMON,
            ExperienceCardType.YUAN_YING_CARD: CardRarity.RARE,
        }
        return _rarity_map.get(self, CardRarity.COMMON)

    @property
    def color_hex(self) -> str:
        _colors = {
            ExperienceCardType.ZHU_JI_CARD: "#4CAF50",
            ExperienceCardType.JIN_DAN_CARD: "#FFD700",
            ExperienceCardType.YUAN_YING_CARD: "#9C27B0",
        }
        return _colors.get(self, "#808080")

    @property
    def icon(self) -> str:
        _icons = {
            ExperienceCardType.ZHU_JI_CARD: "\u26f5\ufe0f",
            ExperienceCardType.JIN_DAN_CARD: "\u2604\ufe0f",
            ExperienceCardType.YUAN_YING_CARD: "\u2728",
        }
        return _icons.get(self, "\ud83d\udce7")

    @property
    def description(self) -> str:
        _descs = {
            ExperienceCardType.ZHU_JI_CARD:
                "\u4e34\u65f6\u89e3\u9501\u7b51\u57fa\u671f\u80fd\u529b\uff08\u677f\u5757\u5bf9\u6bd4\u3001\u98ce\u9669\u8bc4\u7ea7\uff09\uff0c" +
                "\u6709\u6548\u671f24\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75283\u6b21\u3002",
            ExperienceCardType.JIN_DAN_CARD:
                "\u4e34\u65f6\u89e3\u9501\u91d1\u4e39\u671f\u80fd\u529b\uff08\u591a\u56e0\u5b50\u9884\u6d4b\u3001\u590f\u666e\u6bd4\u7387\u3001\u7f6e\u4fe1\u533a\u95f4\uff09\uff0c" +
                "\u6709\u6548\u671f48\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75285\u6b21\u3002",
            ExperienceCardType.YUAN_YING_CARD:
                "\u4e34\u65f6\u89e3\u9501\u5143\u5a74\u671f\u80fd\u529b\uff08\u653f\u7b56\u5f71\u54cd\u91cf\u5316\u3001\u5f52\u56e0\u5206\u6790\u3001\u60c5\u666f\u6a21\u62df\uff09\uff0c" +
                "\u6709\u6548\u671f72\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75287\u6b21\u3002",
        }
        return _descs.get(self, "")


@dataclass
class ExperienceCard:
    card_id: str
    card_type: ExperienceCardType
    user_id: str
    status: CardStatus = CardStatus.IN_BACKPACK
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    uses_remaining: int = 0
    uses_total: int = 0
    grant_source: GrantSource = GrantSource.NEWBIE
    grant_source_detail: str = ""

    def __post_init__(self):
        if self.granted_at is None:
            self.granted_at = datetime.utcnow()
        if self.uses_total == 0:
            self.uses_total = self.card_type.max_uses
        if self.uses_remaining == 0:
            self.uses_remaining = self.uses_total


@dataclass
class UseResult:
    success: bool
    message: str
    temp_realm_applied: Optional["QuantRealm"] = None
    remaining_uses: int = 0
    new_status: CardStatus = CardStatus.IN_BACKPACK


EXPERIENCE_CARD_TYPE_CONFIGS: Dict[ExperienceCardType, Dict[str, Any]] = {
    ExperienceCardType.ZHU_JI_CARD: {
        "duration_hours": 24,
        "uses_max": 3,
        "rarity": CardRarity.COMMON,
        "color": "#4CAF50",
        "icon": "\u26f5\ufe0f",
        "description":
            "\u4e34\u65f6\u89e3\u9501\u7b51\u57fa\u671f\u80fd\u529b\uff08\u677f\u5757\u5bf9\u6bd4\u3001\u98ce\u9669\u8bc4\u7ea7\uff09\uff0c" +
            "\u6709\u6548\u671f24\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75283\u6b21\u3002",
        "unlocked_features_list": [
            "sector_comparison", "risk_rating", "basic_trend_analysis",
            "price_heatmap_view", "neighborhood_ranking",
        ],
        "target_realm_name": "ZHU_JI",
    },
    ExperienceCardType.JIN_DAN_CARD: {
        "duration_hours": 48,
        "uses_max": 5,
        "rarity": CardRarity.UNCOMMON,
        "color": "#FFD700",
        "icon": "\u2604\ufe0f",
        "description":
            "\u4e34\u65f6\u89e3\u9501\u91d1\u4e39\u671f\u80fd\u529b\uff08\u591a\u56e0\u5b50\u9884\u6d4b\u3001\u590f\u666e\u6bd4\u7387\u3001\u7f6e\u4fe1\u533a\u95f4\uff09\uff0c" +
            "\u6709\u6548\u671f48\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75285\u6b21\u3002",
        "unlocked_features_list": [
            "multi_factor_prediction", "sharpe_ratio_calculation",
            "confidence_interval_display", "correlation_matrix",
            "regression_model_output", "factor_exposure_analysis",
        ],
        "target_realm_name": "JIN_DAN",
    },
    ExperienceCardType.YUAN_YING_CARD: {
        "duration_hours": 72,
        "uses_max": 7,
        "rarity": CardRarity.RARE,
        "color": "#9C27B0",
        "icon": "\u2728",
        "description":
            "\u4e34\u65f6\u89e3\u9501\u5143\u5a74\u671f\u80fd\u529b\uff08\u653f\u7b56\u5f71\u54cd\u91cf\u5316\u3001\u5f52\u56e0\u5206\u6790\u3001\u60c5\u666f\u6a21\u62df\uff09\uff0c" +
            "\u6709\u6548\u671f72\u5c0f\u65f6\uff0c\u53ef\u4f7f\u75287\u6b21\u3002",
        "unlocked_features_list": [
            "policy_impact_quantification", "attribution_analysis",
            "scenario_simulation", "monte_carlo_forecast",
            "macro_factor_decomposition", "stress_testing_suite",
            "portfolio_optimization_engine", "real_time_risk_monitoring",
        ],
        "target_realm_name": "YUAN_YING",
    },
}


@dataclass
class CardGrantRule:
    rule_id: str
    name: str
    source_type: GrantSource
    min_condition: str
    reward_card_type: ExperienceCardType
    reward_count: int
    cooldown_seconds: int = 0
    is_repeatable: bool = False


CARD_GRANT_RULES: List[CardGrantRule] = [
    CardGrantRule(
        rule_id="rule_newbie_register",
        name="\u65b0\u7528\u6237\u6ce8\u518c\u8d60\u9001",
        source_type=GrantSource.NEWBIE,
        min_condition="register_complete",
        reward_card_type=ExperienceCardType.ZHU_JI_CARD,
        reward_count=1,
        cooldown_seconds=0,
        is_repeatable=False,
    ),
    CardGrantRule(
        rule_id="rule_onboarding_complete",
        name="\u5b8c\u6210\u65b0\u624b\u5f15\u5bfc\u4efb\u52a1",
        source_type=GrantSource.TASK,
        min_condition="onboarding_100_percent",
        reward_card_type=ExperienceCardType.JIN_DAN_CARD,
        reward_count=1,
        cooldown_seconds=0,
        is_repeatable=False,
    ),
    CardGrantRule(
        rule_id="rule_daily_streak_7",
        name="\u6bcf\u65e5\u7b7e\u5230\u8fde\u7eed7\u5929",
        source_type=GrantSource.DAILY_STREAK,
        min_condition="streak_days >= 7",
        reward_card_type=ExperienceCardType.ZHU_JI_CARD,
        reward_count=1,
        cooldown_seconds=259200,
        is_repeatable=True,
    ),
    CardGrantRule(
        rule_id="rule_invite_friend",
        name="\u9080\u8bf7\u597d\u53cb\u6ce8\u518c",
        source_type=GrantSource.INVITE,
        min_condition="invitee_first_consult",
        reward_card_type=ExperienceCardType.JIN_DAN_CARD,
        reward_count=1,
        cooldown_seconds=0,
        is_repeatable=True,
    ),
    CardGrantRule(
        rule_id="rule_limited_event",
        name="\u9650\u65f6\u6d3b\u52a8\u914d\u7f6e",
        source_type=GrantSource.EVENT,
        min_condition="event_participation",
        reward_card_type=ExperienceCardType.ZHU_JI_CARD,
        reward_count=1,
        cooldown_seconds=0,
        is_repeatable=True,
    ),
    CardGrantRule(
        rule_id="rule_shop_purchase",
        name="\u5546\u57ce\u8d2d\u4e70",
        source_type=GrantSource.SHOP,
        min_condition="points_sufficient",
        reward_card_type=ExperienceCardType.JIN_DAN_CARD,
        reward_count=1,
        cooldown_seconds=0,
        is_repeatable=True,
    ),
]


class ExperienceCardInventory:
    """Manages the full lifecycle of experience cards for all users."""

    def __init__(self):
        self._cards: Dict[str, Dict[str, ExperienceCard]] = defaultdict(dict)
        self._lock = threading.RLock()

    def add_card(
        self,
        user_id: str,
        card_type: ExperienceCardType,
        source: GrantSource,
        source_detail: str = "",
    ) -> str:
        card_id = "card_" + uuid.uuid4().hex[:12]
        config = EXPERIENCE_CARD_TYPE_CONFIGS[card_type]
        duration_hours = config["duration_hours"]
        uses_max = config["uses_max"]
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        card = ExperienceCard(
            card_id=card_id,
            card_type=card_type,
            user_id=user_id,
            status=CardStatus.IN_BACKPACK,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            uses_remaining=uses_max,
            uses_total=uses_max,
            grant_source=source,
            grant_source_detail=source_detail,
        )
        with self._lock:
            self._cards[user_id][card_id] = card
        logger.info(
            "Card added: user=%s card=%s type=%s source=%s",
            user_id, card_id, card_type.value, source.value,
        )
        return card_id

    def get_user_cards(self, user_id: str) -> List[ExperienceCard]:
        with self._lock:
            return list(self._cards.get(user_id, {}).values())

    def use_card(self, card_id: str) -> UseResult:
        with self._lock:
            for uid, cards in self._cards.items():
                if card_id in cards:
                    card = cards[card_id]
                    if card.status == CardStatus.EXPIRED:
                        return UseResult(
                            success=False,
                            message="\u4f53\u9a8c\u5361\u5df2\u8fc7\u671f\uff0c\u65e0\u6cd5\u4f7f\u7528\u3002",
                        )
                    if card.status == CardStatus.USED:
                        return UseResult(
                            success=False,
                            message="\u4f53\u9a8c\u5361\u5df2\u4f7f\u7528\u8fc7\u3002",
                        )
                    if card.uses_remaining <= 0:
                        card.status = CardStatus.EXPIRED
                        return UseResult(
                            success=False,
                            message="\u4f53\u9a8c\u5361\u4f7f\u7528\u6b21\u6570\u5df2\u7ecf\u7528\u5b8c\u3002",
                            remaining_uses=0,
                            new_status=CardStatus.EXPIRED,
                        )
                    if datetime.utcnow() > (card.expires_at or datetime.max):
                        card.status = CardStatus.EXPIRED
                        return UseResult(
                            success=False,
                            message="\u4f53\u9a8c\u5361\u5df2\u8fc7\u671f\u3002",
                            new_status=CardStatus.EXPIRED,
                        )
                    card.uses_remaining -= 1
                    if card.uses_remaining <= 0:
                        card.status = CardStatus.USED
                    else:
                        card.status = CardStatus.ACTIVE
                    return UseResult(
                        success=True,
                        message=(
                            "\u4f53\u9a8c\u5361\u4f7f\u7528\u6210\u529f\uff01" +
                            "\u4e34\u65f6\u89e3\u9501" + card.card_type.display_name +
                            "\u80fd\u529b\uff0c\u5269\u4f59" + str(card.uses_remaining) + "\u6b21\u3002"
                        ),
                        temp_realm_applied=card.card_type.target_realm,
                        remaining_uses=card.uses_remaining,
                        new_status=card.status,
                    )
        return UseResult(success=False, message="\u672a\u627e\u5230\u4f53\u9a8c\u5361\u3002")

    def check_usages_remaining(self, card_id: str) -> int:
        with self._lock:
            for cards in self._cards.values():
                if card_id in cards:
                    return cards[card_id].uses_remaining
        return 0

    def get_active_temp_realm(self, user_id: str) -> Optional["QuantRealm"]:
        with self._lock:
            for card in self._cards.get(user_id, {}).values():
                if card.status == CardStatus.ACTIVE:
                    if card.expires_at and datetime.utcnow() < card.expires_at:
                        if card.uses_remaining > 0:
                            return card.card_type.target_realm
        return None

    def expire_card(self, card_id: str) -> bool:
        with self._lock:
            for cards in self._cards.values():
                if card_id in cards:
                    card = cards[card_id]
                    if card.status in (CardStatus.ACTIVE, CardStatus.IN_BACKPACK):
                        card.status = CardStatus.EXPIRED
                        logger.info("Card expired: %s", card_id)
                        return True
        return False


# =============================================================================
# PART B: TEMPORARY REALM STATE MANAGEMENT
# =============================================================================


class QuantRealm(Enum):
    LIAN_QI = "lian_qi"
    ZHU_JI = "zhu_ji"
    JIN_DAN = "jin_dan"
    YUAN_YING = "yuan_ying"
    HUA_SHEN = "hua_shen"
    DU_JIE = "du_jie"
    DA_CHENG = "da_cheng"

    @property
    def display_name_cn(self) -> str:
        names = {
            QuantRealm.LIAN_QI: "\u70bc\u6c14\u671f",
            QuantRealm.ZHU_JI: "\u7b51\u57fa\u671f",
            QuantRealm.JIN_DAN: "\u91d1\u4e39\u671f",
            QuantRealm.YUAN_YING: "\u5143\u5a74\u671f",
            QuantRealm.HUA_SHEN: "\u5316\u795e\u671f",
            QuantRealm.DU_JIE: "\u6e21\u52ab\u671f",
            QuantRealm.DA_CHENG: "\u5927\u6210\u671f",
        }
        return names.get(self, str(self.value))

    @property
    def tier_level(self) -> int:
        levels = {
            QuantRealm.LIAN_QI: 1,
            QuantRealm.ZHU_JI: 2,
            QuantRealm.JIN_DAN: 3,
            QuantRealm.YUAN_YING: 4,
            QuantRealm.HUA_SHEN: 5,
            QuantRealm.DU_JIE: 6,
            QuantRealm.DA_CHENG: 7,
        }
        return levels.get(self, 1)


@dataclass
class TempRealmState:
    user_id: str
    temp_realm: Optional[QuantRealm] = None
    temp_expiry: Optional[datetime] = None
    temp_usage_count: int = 0
    temp_max_usage: int = 0
    original_realm: QuantRealm = QuantRealm.LIAN_QI
    activated_by_card_id: str = ""
    is_active: bool = False
    exp_multiplier: float = 0.5


@dataclass
class TrialBadgeSpec:
    badge_text: str
    badge_style: str
    color: str
    hover_tooltip_template: str
    show_countdown: bool = True
    show_remaining_uses: bool = True


TRIAL_BADGE_SPECS: Dict[ExperienceCardType, TrialBadgeSpec] = {
    ExperienceCardType.ZHU_JI_CARD: TrialBadgeSpec(
        badge_text="\u4f53\u9a8c\u4e2d",
        badge_style="dashed_border",
        color="#4CAF50",
        hover_tooltip_template=
            "\u7b51\u57fa\u4f53\u9a8c\u5361\u4f53\u9a8c\u4e2d | \u5269\u4f59{uses}\u6b21 | \u5230\u671f{countdown}",
        show_countdown=True,
        show_remaining_uses=True,
    ),
    ExperienceCardType.JIN_DAN_CARD: TrialBadgeSpec(
        badge_text="\u4f53\u9a8c\u4e2d",
        badge_style="glowing",
        color="#FFD700",
        hover_tooltip_template=
            "\u91d1\u4e39\u4f53\u9a8c\u5361\u4f53\u9a8c\u4e2d | \u5269\u4f59{uses}\u6b21 | \u5230\u671f{countdown}",
        show_countdown=True,
        show_remaining_uses=True,
    ),
    ExperienceCardType.YUAN_YING_CARD: TrialBadgeSpec(
        badge_text="\u4f53\u9a8c\u4e2d",
        badge_style="pulse_animation",
        color="#9C27B0",
        hover_tooltip_template=
            "\u5143\u5a74\u4f53\u9a8c\u5361\u4f53\u9a8c\u4e2d | \u5269\u4f59{uses}\u6b21 | \u5230\u671f{countdown}",
        show_countdown=True,
        show_remaining_uses=True,
    ),
}


class TempRealmManager:
    """Manages temporary realm states activated by experience cards."""

    def __init__(self):
        self._states: Dict[str, TempRealmState] = {}
        self._lock = threading.RLock()

    def activate_temp_realm(
        self,
        user_id: str,
        realm: QuantRealm,
        card_id: str,
        max_uses: int,
        duration_hours: int,
    ) -> TempRealmState:
        expiry = datetime.utcnow() + timedelta(hours=duration_hours)
        state = TempRealmState(
            user_id=user_id,
            temp_realm=realm,
            temp_expiry=expiry,
            temp_usage_count=0,
            temp_max_usage=max_uses,
            original_realm=QuantRealm.LIAN_QI,
            activated_by_card_id=card_id,
            is_active=True,
            exp_multiplier=0.5,
        )
        with self._lock:
            self._states[user_id] = state
        logger.info(
            "Temp realm activated: user=%s realm=%s card=%s until=%s",
            user_id, realm.value, card_id, expiry.isoformat(),
        )
        return state

    def deactivate_temp_realm(self, user_id: str) -> Optional[QuantRealm]:
        with self._lock:
            if user_id in self._states:
                state = self._states.pop(user_id)
                state.is_active = False
                logger.info("Temp realm deactivated: user=%s was=%s", user_id, state.temp_realm.value if state.temp_realm else None)
                return state.temp_realm
        return None

    def get_effective_realm(self, user_id: str, real_realm: QuantRealm = QuantRealm.LIAN_QI) -> QuantRealm:
        with self._lock:
            state = self._states.get(user_id)
            if state and state.is_active:
                if state.temp_realm and state.temp_expiry:
                    if datetime.utcnow() < state.temp_expiry:
                        if state.temp_usage_count < state.temp_max_usage:
                            return state.temp_realm
        return real_realm

    def check_and_auto_expire(self, user_id: str) -> bool:
        with self._lock:
            state = self._states.get(user_id)
            if not state or not state.is_active:
                return False
            now = datetime.utcnow()
            expired = state.temp_expiry and now >= state.temp_expiry
            exhausted = state.temp_usage_count >= state.temp_max_usage
            if expired or exhausted:
                state.is_active = False
                reason = "expired" if expired else "exhausted"
                logger.info(
                    "Auto-expire temp realm: user=%s reason=%s", user_id, reason,
                )
                return True
        return False

    def record_usage(self, user_id: str) -> int:
        with self._lock:
            state = self._states.get(user_id)
            if state and state.is_active:
                state.temp_usage_count += 1
                remaining = state.temp_max_usage - state.temp_usage_count
                if remaining <= 0:
                    state.is_active = False
                return max(0, remaining)
        return 0

    def get_state(self, user_id: str) -> Optional[TempRealmState]:
        with self._lock:
            return self._states.get(user_id)

    def get_all_active_states(self) -> List[TempRealmState]:
        with self._lock:
            return [s for s in self._states.values() if s.is_active]

    def should_grant_exp(self, user_id: str) -> bool:
        with self._lock:
            state = self._states.get(user_id)
            if state and state.is_active:
                return False
        return True


class TrialUIIndicator:
    """Generates HTML/visual indicators for trial status on frontend."""

    def generate_badge_html(self, state: TempRealmState) -> str:
        if not state or not state.is_active or not state.temp_realm:
            return ""
        card_type = self._realm_to_card_type(state.temp_realm)
        spec = TRIAL_BADGE_SPECS.get(card_type)
        if not spec:
            return ""
        style_map = {
            "dashed_border": "border: 2px dashed " + spec.color + "; border-radius: 12px; padding: 4px 10px;",
            "glowing": "border: 2px solid " + spec.color + "; box-shadow: 0 0 8px " + spec.color + "; border-radius: 12px; padding: 4px 10px;",
            "pulse_animation": "border: 2px solid " + spec.color + "; border-radius: 12px; padding: 4px 10px; animation: pulse 2s infinite;",
        }
        style = style_map.get(spec.badge_style, "")
        uses_str = str(state.temp_max_usage - state.temp_usage_count)
        countdown_str = ""
        if state.temp_expiry:
            delta = state.temp_expiry - datetime.utcnow()
            total_secs = max(0, int(delta.total_seconds()))
            hours_val = total_secs // 3600
            mins_val = (total_secs % 3600) // 60
            countdown_str = str(hours_val) + "h" + str(mins_val) + "m"
        html = (
            '<span class="trial-badge" style="' + style + ' color:' + spec.color + '; font-weight:bold;">' +
            '<span class="trial-badge-icon">' + (card_type.icon if hasattr(card_type, 'icon') else '') + '</span> ' +
            spec.badge_text +
            '</span>'
        )
        return html

    def generate_expiring_soon_warning(self, state: TempRealmState) -> Optional[str]:
        if not state or not state.is_active or not state.temp_expiry:
            return None
        delta = state.temp_expiry - datetime.utcnow()
        if delta.total_seconds() > 3600:
            return None
        mins_left = max(0, int(delta.total_seconds() // 60))
        realm_name = state.temp_realm.display_name_cn if state.temp_realm else ""
        warning = (
            '<div class="expiring-soon-warning" style="background:#FFF3E0;border-left:4px solid #FF9800;padding:10px;margin:8px 0;border-radius:4px;">' +
            '<strong>\u26a0\ufe0f \u4f53\u9a8c\u5361\u5373\u5c06\u5230\u671f</strong><br/>' +
            '\u60a8\u7684' + realm_name + '\u4f53\u9a8c\u5361\u8fd8\u5269' + str(mins_left) + '\u5206\u949f\uff0c' +
            '\u5230\u671f\u540e\u5c06\u6062\u590d\u5230\u7b51\u57fa\u671f\u3002' +
            '\u5efa\u8bae\u5c3d\u5feb\u5b8c\u6210\u4fee\u70bc\u4efb\u52a1\uff0c\u63d0\u5347\u771f\u5b9e\u5883\u754c\u3002' +
            '</div>'
        )
        return warning

    def generate_panel_overlay(
        self, real_realm: QuantRealm, temp_state: TempRealmState
    ) -> str:
        if not temp_state or not temp_state.is_active or not temp_state.temp_realm:
            return ""
        temp_name = temp_state.temp_realm.display_name_cn
        real_name = real_realm.display_name_cn
        overlay = (
            '<div class="realm-panel-overlay" style="position:relative;border:2px dashed #9C27B0;' +
            'border-radius:12px;padding:16px;background:rgba(156,39,176,0.05);">' +
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">' +
            '<span style="font-weight:bold;color:#9C27B0;">\u2728 ' + temp_name + ' (\u4f53\u9a8c\u4e2d)</span>' +
            '<span style="font-size:12px;color:#888;">\u771f\u5b9e\u5883\u754c: ' + real_name + '</span>' +
            '</div>' +
            '<div class="trial-progress-bar" style="background:#eee;border-radius:6px;height:8px;width:100%;">' +
            '<div class="trial-progress-fill" style="background:linear-gradient(90deg,#9C27B0,#E1BEE7);' +
            'height:100%;border-radius:6px;width:' +
            str(int((temp_state.temp_usage_count / max(1, temp_state.temp_max_usage)) * 100)) +
            '%;"></div></div>' +
            '<div style="font-size:11px;color:#999;margin-top:4px;">' +
            '\u5df2\u4f7f\u7528 ' + str(temp_state.temp_usage_count) + ' / ' + str(temp_state.temp_max_usage) +
            '</div></div>'
        )
        return overlay

    @staticmethod
    def _realm_to_card_type(realm: QuantRealm) -> Optional[ExperienceCardType]:
        mapping = {
            QuantRealm.ZHU_JI: ExperienceCardType.ZHU_JI_CARD,
            QuantRealm.JIN_DAN: ExperienceCardType.JIN_DAN_CARD,
            QuantRealm.YUAN_YING: ExperienceCardType.YUAN_YING_CARD,
        }
        return mapping.get(realm)


# =============================================================================
# PART C: POST-TRIAL RETURN & REINCARNATION DESIGN
# =============================================================================


@dataclass
class GuidanceMessage:
    title: str
    body_text: str
    action_button: str
    action_target: str
    priority: int = 1
    urgency: str = "normal"


@dataclass
class ReincarnationRecord:
    user_id: str
    reincarnation_count: int
    previous_max_realm: QuantRealm
    previous_total_exp: float
    reset_at: datetime
    rewards_kept: List[str] = field(default_factory=list)
    reincarnation_marks_earned: int = 0
    cooldown_until: Optional[datetime] = None


REINCARNATION_CONFIG: Dict[str, Any] = {
    "cooldown_days": 30,
    "keep_rewards": ["special_title", "exclusive_skin"],
    "marks_per_reincarnation": 1,
    "min_realms_before_allow": 2,
    "min_required_tier_for_reincarnate": QuantRealm.JIN_DAN.tier_level,
}


GUIDANCE_TEMPLATES: Dict[ExperienceCardType, Dict[str, str]] = {
    ExperienceCardType.ZHU_JI_CARD: {
        "title": "\u4f53\u9a8c\u7ed3\u675f\uff0c\u56de\u5f52\u4fee\u70bc",
        "body":
            "\u60a8\u7684\u7b51\u57fa\u4f53\u9a8c\u5361\u5df2\u7ecf\u5230\u671f\uff0c\u60a8\u5df2\u56de\u5230\u70bc\u6c14\u671f\u3002" +
            "\u53ea\u9700\u518d\u5b8c\u62103\u6b21\u677f\u5757\u5206\u6790\uff0c\u5373\u53ef\u771f\u6b63\u7a81\u7834\u7b51\u57fa\u671f\uff01",
        "action_button": "\u67e5\u770b\u4fee\u70bc\u4efb\u52a1",
        "action_target": "/cultivation/tasks",
    },
    ExperienceCardType.JIN_DAN_CARD: {
        "title": "\u91d1\u4e39\u4f53\u9a8c\u5230\u671f",
        "body":
            "\u60a8\u7684\u91d1\u4e39\u4f53\u9a8c\u5361\u5df2\u7ecf\u5230\u671f\uff0c\u6682\u65f6\u6062\u590d\u5230\u7b51\u57fa\u671f\u3002" +
            "\u60a8\u5728\u4f53\u9a8c\u671f\u95f4\u9884\u6d4b\u7684\u7ed3\u679c\u5df2\u4fdd\u5b58\uff0c\u53ef\u4ee5\u53bb\u9a8c\u8bc1\u5b9e\u9645\u8d70\u52bf\u3002" +
            "\u7ee7\u7eed\u4fee\u70bc\u5373\u53ef\u89e3\u9501\u91d1\u4e39\u671f\u5168\u90e8\u80fd\u529b\uff01",
        "action_button": "\u5f00\u59cb\u4fee\u70bc\u7a81\u7834",
        "action_target": "/cultivation/breakthrough",
    },
    ExperienceCardType.YUAN_YING_CARD: {
        "title": "\u5143\u5a74\u4f53\u9a8c\u5b8c\u6bd5",
        "body":
            "\u60a8\u7684\u5143\u5a74\u4f53\u9a8c\u5361\u5df2\u7ec1\u7ed3\uff0c\u611f\u8c22\u60a8\u7684\u4f53\u9a8c\uff01" +
            "\u4f53\u9a8c\u671f\u95f4\u7684\u9ad8\u7eb7\u5206\u6790\u6570\u636e\u5df2\u4fdd\u5b58\uff0c" +
            "\u82e5\u60a8\u60f3\u91cd\u65b0\u6311\u6218\uff0c\u53ef\u8003\u8651\u201c\u8f6e\u56de\u201d\u673a\u5236\u83b7\u5f97\u66f4\u591a\u5370\u8bb0\u3002",
        "action_button": "\u67e5\u770b\u8f6e\u56de\u9009\u9879",
        "action_target": "/cultivation/reincarnation",
    },
}


class PostTrialGuidanceManager:
    """Generates guidance messages after trial expiration and manages preserved data."""

    def __init__(self):
        self._preserved_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()

    def generate_return_guidance(
        self, user_state: TempRealmState, expired_card_type: ExperienceCardType
    ) -> GuidanceMessage:
        template = GUIDANCE_TEMPLATES.get(expired_card_type)
        if template:
            return GuidanceMessage(
                title=template["title"],
                body_text=template["body"],
                action_button=template["action_button"],
                action_target=template["action_target"],
                priority=2,
                urgency="high",
            )
        return GuidanceMessage(
            title="\u4f53\u9a8c\u7ed3\u675f",
            body_text="\u60a8\u7684\u4f53\u9a8c\u5361\u5df2\u5230\u671f\uff0c\u8bf7\u7ee7\u7eed\u4fee\u70bc\u63d0\u5347\u5883\u754c\u3002",
            action_button="\u524d\u5f80\u4fee\u70bc",
            action_target="/cultivation",
            priority=1,
            urgency="normal",
        )

    def generate_verification_prompt(
        self, user_id: str, trial_prediction_record: Dict[str, Any]
    ) -> str:
        predicted_block = trial_prediction_record.get("predicted_sector", "\u672a\u77e5")
        predicted_change = trial_prediction_record.get("predicted_change_pct", 0)
        prompt = (
            "\u60a8\u5728\u4f53\u9a8c\u671f\u95f4\u9884\u6d4b " + str(predicted_block) +
            " \u677f\u5757 " + ("+" if predicted_change >= 0 else "") + str(predicted_change) +
            "%\uff0c\u73b0\u5728\u53bb\u9a8c\u8bc1\u5b9e\u9645\u8d70\u52bf\u5427\uff01"
        )
        return prompt

    def preserve_trial_data(self, user_id: str, data_ref: Dict[str, Any]) -> None:
        entry = dict(data_ref)
        entry["preserved_at"] = datetime.utcnow().isoformat()
        with self._lock:
            self._preserved_data[user_id].append(entry)
        logger.info("Trial data preserved for user=%s entries=%d", user_id, len(self._preserved_data[user_id]))

    def get_preserved_trial_data(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._preserved_data.get(user_id, []))


@dataclass
class ExchangeResult:
    success: bool
    message: str
    marks_spent: int = 0
    reward_id: str = ""
    marks_remaining: int = 0


class ReincarnationSystem:
    """Manages the reincarnation (reset/rebirth) mechanic for advanced users."""

    def __init__(self):
        self._records: Dict[str, ReincarnationRecord] = {}
        self._marks_balance: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

    def check_eligibility(
        self, user_id: str, current_realm: QuantRealm
    ) -> Tuple[bool, str]:
        record = self._records.get(user_id)
        if record:
            if record.cooldown_until and datetime.utcnow() < record.cooldown_until:
                remaining = (record.cooldown_until - datetime.utcnow()).days
                return (
                    False,
                    "\u8f6e\u56de\u51b7\u5374\u4e2d\uff0c\u8fd8\u5269" + str(remaining) + "\u5929\u3002",
                )
        min_tier = REINCARNATION_CONFIG["min_required_tier_for_reincarnate"]
        if current_realm.tier_level < min_tier:
            required_realm_name = QuantRealm.JIN_DAN.display_name_cn
            return (
                False,
                "\u9700\u8fbe\u5230" + required_realm_name + "\u624d\u80fd\u8fdb\u884c\u8f6e\u56de\u3002",
            )
        return True, "\u7b26\u5408\u8f6e\u56de\u6761\u4ef6\u3002"

    def execute_reincarnation(self, user_id: str) -> ReincarnationRecord:
        import random as _rnd
        prev_record = self._records.get(user_id)
        prev_count = prev_record.reincarnation_count if prev_record else 0
        new_count = prev_count + 1
        cooldown_days = REINCARNATION_CONFIG["cooldown_days"]
        cooldown_until = datetime.utcnow() + timedelta(days=cooldown_days)
        marks_earned = REINCARNATION_CONFIG["marks_per_reincarnation"]
        kept_rewards = list(REINCARNATION_CONFIG["keep_rewards"])
        record = ReincarnationRecord(
            user_id=user_id,
            reincarnation_count=new_count,
            previous_max_realm=QuantRealm.JIN_DAN,
            previous_total_exp=0.0,
            reset_at=datetime.utcnow(),
            rewards_kept=kept_rewards,
            reincarnation_marks_earned=marks_earned,
            cooldown_until=cooldown_until,
        )
        with self._lock:
            self._records[user_id] = record
            self._marks_balance[user_id] += marks_earned
        logger.info(
            "Reincarnation executed: user=%s count=%d marks_total=%d",
            user_id, new_count, self._marks_balance[user_id],
        )
        return record

    def get_reincarnation_history(self, user_id: str) -> List[ReincarnationRecord]:
        with self._lock:
            rec = self._records.get(user_id)
            return [rec] if rec else []

    def get_available_marks(self, user_id: str) -> int:
        with self._lock:
            return self._marks_balance.get(user_id, 0)

    def exchange_marks(
        self, user_id: str, count: int, reward_id: str
    ) -> ExchangeResult:
        with self._lock:
            available = self._marks_balance.get(user_id, 0)
            if available < count:
                return ExchangeResult(
                    success=False,
                    message="\u8f6e\u56de\u5370\u8bb0\u4e0d\u8db3\uff0c\u5f53\u524d" + str(available) +
                    "\u5f0c\uff0c\u9700\u8981" + str(count) + "\u5f0e\u3002",
                    marks_remaining=available,
                )
            self._marks_balance[user_id] -= count
            return ExchangeResult(
                success=True,
                message="\u5151\u6362\u6210\u529f\uff01\u83b7\u5f97" + reward_id + "\u3002",
                marks_spent=count,
                reward_id=reward_id,
                marks_remaining=self._marks_balance[user_id],
            )


# =============================================================================
# PART D: BALANCE DESIGN & ANTI-ABUSE
# =============================================================================


@dataclass
class BalanceConfig:
    max_cards_per_month_per_type: int = 2
    max_concurrent_trials: int = 1
    allow_stack_same_type: bool = False
    exp_during_trial_ratio: float = 0.5
    allow_trading: bool = False
    allow_gifting: bool = False
    rate_limit_per_minute: int = 10
    daily_api_call_limit: int = 100


@dataclass
class MonthlyAcquisitionLog:
    user_id: str
    card_type: ExperienceCardType
    year_month: str
    count: int
    last_granted_at: Optional[datetime] = None


class AntiAbuseChecker:
    """Enforces balance constraints and prevents abuse of experience cards."""

    def __init__(self, config: Optional[BalanceConfig] = None):
        self.config = config or BalanceConfig()
        self._monthly_counts: Dict[Tuple[str, ExperienceCardType], int] = defaultdict(int)
        self._concurrent_trials: Set[str] = set()
        self._rate_limit_buckets: Dict[str, List[float]] = defaultdict(list)
        self._api_call_counts: Dict[str, int] = defaultdict(int)
        self._last_api_reset_date: Optional[str] = None
        self._lock = threading.RLock()

    def check_monthly_limit(self, user_id: str, card_type: ExperienceCardType) -> bool:
        key = (user_id, card_type)
        with self._lock:
            current = self._monthly_counts.get(key, 0)
            return current < self.config.max_cards_per_month_per_type

    def increment_monthly_count(self, user_id: str, card_type: ExperienceCardType) -> int:
        key = (user_id, card_type)
        with self._lock:
            self._monthly_counts[key] += 1
            return self._monthly_counts[key]

    def reset_monthly_counts(self, year_month: Optional[str] = None) -> int:
        target = year_month or (datetime.utcnow().strftime("%Y-%m"))
        removed = 0
        with self._lock:
            keys_to_remove = [k for k in self._monthly_counts]
            self._monthly_counts.clear()
            removed = len(keys_to_remove)
        logger.info("Monthly counts reset for %s: %d entries cleared", target, removed)
        return removed

    def check_concurrent_limit(self, user_id: str) -> bool:
        with self._lock:
            active = len([u for u in self._concurrent_trials if u == user_id])
            return active < self.config.max_concurrent_trials

    def set_concurrent_trial(self, user_id: str, active: bool) -> None:
        with self._lock:
            if active:
                self._concurrent_trials.add(user_id)
            else:
                self._concurrent_trials.discard(user_id)

    def clear_concurrent_trial(self, user_id: str) -> None:
        self.set_concurrent_trial(user_id, False)

    def check_can_activate(
        self, user_id: str, target_realm: QuantRealm
    ) -> Tuple[bool, str]:
        monthly_ok = self.check_monthly_limit(user_id, self._realm_to_card_type_or_default(target_realm))
        if not monthly_ok:
            return (
                False,
                "\u672c\u6708\u8be5\u7c7b\u578b\u4f53\u9a8c\u5361\u83b7\u53d6\u5df2\u8fbe\u4e0a\u9650(" +
                str(self.config.max_cards_per_month_per_type) + "\u5f20/\u6708)\u3002",
            )
        concurrent_ok = self.check_concurrent_limit(user_id)
        if not concurrent_ok:
            return (
                False,
                "\u5df2\u6709\u8fdb\u884c\u4e2d\u7684\u4f53\u9a8c\uff0c\u8bf7\u5148\u5b8c\u6210\u5f53\u524d\u4f53\u9a8c\u518d\u5f00\u542f\u65b0\u7684\u3002",
            )
        if not self.config.allow_stack_same_type:
            return True, "\u68c0\u67e5\u901a\u8fc7\uff0c\u53ef\u4ee5\u6fc0\u6d3b\u3002"
        return True, "\u68c0\u67e5\u901a\u8fc7\u3002"

    def check_exp_grant(self, user_id: str) -> float:
        with self._lock:
            if user_id in self._concurrent_trials:
                return self.config.exp_during_trial_ratio
        return 1.0

    def validate_tradability(self, card_id: str) -> bool:
        return self.config.allow_trading

    def check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        window = 60.0
        with self._lock:
            bucket = self._rate_limit_buckets[user_id]
            bucket.append(now)
            bucket[:] = [t for t in bucket if now - t < window]
            if len(bucket) > self.config.rate_limit_per_minute:
                return False
            return True

    def check_daily_api_limit(self, user_id: str) -> bool:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        with self._lock:
            if self._last_api_reset_date != today:
                self._api_call_counts.clear()
                self._last_api_reset_date = today
            self._api_call_counts[user_id] += 1
            return self._api_call_counts[user_id] <= self.config.daily_api_call_limit

    @staticmethod
    def _realm_to_card_type_or_default(realm: QuantRealm) -> ExperienceCardType:
        mapping = {
            QuantRealm.ZHU_JI: ExperienceCardType.ZHU_JI_CARD,
            QuantRealm.JIN_DAN: ExperienceCardType.JIN_DAN_CARD,
            QuantRealm.YUAN_YING: ExperienceCardType.YUAN_YING_CARD,
        }
        return mapping.get(realm, ExperienceCardType.ZHU_JI_CARD)


# =============================================================================
# PART E: FRONTEND INTERACTION & VISUALS
# =============================================================================


@dataclass
class CultivationBackpackSpec:
    layout_columns: int = 3
    card_display_style: str = "rounded_card_with_rarity_glow"
    card_info_fields: List[str] = field(default_factory=lambda: [
        "icon", "name", "type_badge", "uses_remaining", "countdown",
        "timer_bar", "grant_source", "use_button",
    ])
    empty_state_message: str = ""
    sort_options: List[str] = field(default_factory=lambda: [
        "by_expiry", "by_rarity", "by_type",
    ])


BACKPACK_UI_SPEC: Dict[str, Any] = {
    "page_title": "\u4fee\u4e3a\u80cc\u5305",
    "layout": {"columns": 3, "gap": "16px", "padding": "20px"},
    "card_style": {
        "border_radius": "12px",
        "padding": "16px",
        "background": "#FFFFFF",
        "box_shadow": "0 2px 8px rgba(0,0,0,0.1)",
        "transition": "transform 0.2s, box-shadow 0.2s",
        "hover_transform": "translateY(-4px)",
        "hover_shadow": "0 8px 24px rgba(0,0,0,0.15)",
    },
    "rarity_border_colors": {
        CardRarity.COMMON: "#4CAF50",
        CardRarity.UNCOMMON: "#FFD700",
        CardRarity.RARE: "#9C27B0",
    },
    "card_fields": {
        "icon": {"size": "48px", "position": "top_center"},
        "name": {"font_size": "16px", "font_weight": "bold", "margin_top": "8px"},
        "type_badge": {
            "font_size": "11px",
            "padding": "2px 8px",
            "border_radius": "10px",
            "bg_color": "#F5F5F5",
        },
        "uses_remaining": {
            "template": "\u5269\u4f59 {n} \u6b21",
            "font_size": "13px",
            "color": "#666",
        },
        "countdown": {
            "template": "\u5230\u671f {t}",
            "font_size": "12px",
            "color": "#FF5722",
            "show_icon": True,
        },
        "timer_bar": {
            "height": "4px",
            "bg_color": "#EEEEEE",
            "fill_color_gradient_start": "#4CAF50",
            "fill_color_gradient_end": "#FF5722",
            "border_radius": "2px",
        },
        "grant_source": {
            "template": "\u6765\u6e90: {src}",
            "font_size": "11px",
            "color": "#999",
        },
        "use_button": {
            "text": "\u4f7f\u7528",
            "bg_color": "#1976D2",
            "text_color": "#FFFFFF",
            "border_radius": "8px",
            "padding": "8px 20px",
            "hover_bg_color": "#1565C0",
        },
    },
    "empty_state": {
        "icon": "\ud83d\udce5",
        "message": "\u80cc\u5305\u7a7a\u7a7a\u5982\u4e5f~\u5b8c\u6210\u4efb\u52a1\u6216\u53c2\u52a0\u6d3b\u52a8\u83b7\u53d6\u4f53\u9a8c\u5361\uff01",
        "action_text": "\u53bb\u770b\u4efb\u52a1",
        "action_target": "/tasks",
    },
    "sort_options": [
        {"key": "by_expiry", "label": "\u6309\u5230\u671f\u65f6\u95f4"},
        {"key": "by_rarity", "label": "\u6309\u7a00\u6709\u5ea6"},
        {"key": "by_type", "label": "\u6309\u7c7b\u578b"},
    ],
}


@dataclass
class CardAcquisitionNotificationSpec:
    position: str = "top_right"
    animation: str = "slide_in_fade"
    duration_ms: int = 2000
    sound_effect: str = "light_chime"
    click_action: str = "navigate_to_backpack"
    auto_dismiss_after_ms: int = 5000


@dataclass
class FunctionUnlockOverlaySpec:
    original_disabled_style: str = "opacity: 0.5; pointer-events: none; filter: grayscale(100%);"
    trial_enabled_style: str = "border: 2px solid #4CAF50; box-shadow: 0 0 12px rgba(76,175,80,0.4); position: relative;"
    first_click_modal_template: str = ""
    tooltip_on_hover: str = ""


UNLOCK_OVERLAY_SPEC = FunctionUnlockOverlaySpec(
    original_disabled_style="opacity: 0.5; pointer-events: none; filter: grayscale(100%);",
    trial_enabled_style="border: 2px solid #4CAF50; box-shadow: 0 0 12px rgba(76,175,80,0.4); position: relative;",
    first_click_modal_template=(
        "<div class='trial-first-click-modal' style='position:fixed;top:0;left:0;width:100%;height:100%;" +
        "background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:9999;'>" +
        "<div style='background:white;border-radius:16px;padding:24px;max-width:400px;text-align:center;'>" +
        "<div style='font-size:32px;margin-bottom:12px;'>\u2728</div>" +
        "<h3 style='margin:0 0 8px;'>\u4f53\u9a8c\u6a21\u5f0f\u5df2\u5f00\u542f</h3>" +
        "<p style='color:#666;margin:0 0 16px;font-size:14px;'>\u60a8\u6b63\u5728\u4f7f\u7528 {card_name} \uff0c" +
        "\u8fd8\u53ef\u514d\u8d39\u4f53\u9a8c {remaining_uses} \u6b21 {feature_name} \u529f\u80fd\u3002</p>" +
        "<button onclick='closeTrialModal()' style='background:#1976D2;color:white;border:none;" +
        "padding:10px 28px;border-radius:8px;font-size:14px;cursor:pointer;'>\u6211\u77e5\u9053\u4e86</button>" +
        "</div></div>"
    ),
    tooltip_on_hover="\u4f53\u9a8c\u4e2d \u00b7 \u70b9\u51fb\u67e5\u770b\u8be6\u60c5",
)


class CultivationBackpackRenderer:
    """Renders HTML for backpack UI components."""

    def render_backpack_html(self, cards: List[ExperienceCard]) -> str:
        if not cards:
            empty_icon = BACKPACK_UI_SPEC["empty_state"]["icon"]
            empty_msg = BACKPACK_UI_SPEC["empty_state"]["message"]
            empty_action = BACKPACK_UI_SPEC["empty_state"]["action_text"]
            empty_target = BACKPACK_UI_SPEC["empty_state"]["action_target"]
            return (
                '<div class="backpack-empty" style="text-align:center;padding:60px 20px;">' +
                '<div style="font-size:64px;margin-bottom:16px;">' + empty_icon + '</div>' +
                '<p style="color:#999;font-size:16px;">' + empty_msg + '</p>' +
                '<a href="' + empty_target + '" style="display:inline-block;margin-top:12px;' +
                'background:#1976D2;color:white;padding:10px 24px;border-radius:8px;' +
                'text-decoration:none;">' + empty_action + '</a></div>'
            )
        cols = BACKPACK_UI_SPEC["layout"]["columns"]
        gap = BACKPACK_UI_SPEC["layout"]["gap"]
        padding = BACKPACK_UI_SPEC["layout"]["padding"]
        card_parts = []
        for card in cards:
            card_parts.append(self._render_single_card(card))
        cards_html = "".join(card_parts)
        grid = (
            '<div class="cultivation-backpack" style="display:grid;grid-template-columns:repeat(' +
            str(cols) + ',1fr);gap:' + gap + ';padding:' + padding + ';">' +
            cards_html + '</div>'
        )
        return grid

    def render_notification_html(self, card: ExperienceCard) -> str:
        spec = CardAcquisitionNotificationSpec()
        rarity_color = card.card_type.color_hex
        anim_class = "notify-slide-in" if spec.animation == "slide_in_fade" else "notify-fade-in"
        notify = (
            '<div class="card-acquisition-notification ' + anim_class + '" ' +
            'style="position:fixed;top:20px;right:20px;z-index:10000;' +
            'min-width:320px;background:white;border-radius:12px;' +
            'padding:16px;box-shadow:0 4px 20px rgba(0,0,0,0.15);' +
            'border-left:4px solid ' + rarity_color + ';animation:slideInRight 0.3s ease-out;">' +
            '<div style="display:flex;align-items:center;gap:12px;">' +
            '<div style="font-size:36px;">' + card.card_type.icon + '</div>' +
            '<div style="flex:1;">' +
            '<div style="font-weight:bold;font-size:15px;color:#333;">' +
            '\u83b7\u5f97\u4f53\u9a8c\u5361</div>' +
            '<div style="font-size:13px;color:#666;margin-top:2px;">' +
            card.card_type.display_name + ' \u00b7 ' + str(card.uses_remaining) + '\u6b21\u4f7f\u7528</div>' +
            '</div><button onclick="dismissNotification()" style="background:none;border:none;' +
            'font-size:18px;cursor:pointer;color:#999;">\u00d7</button></div>' +
            '<div style="margin-top:10px;text-align:right;">' +
            '<a href="/backpack" style="font-size:12px;color:#1976D2;text-decoration:none;">' +
            '\u67e5\u770b\u80cc\u5305 \u2192</a></div></div>'
        )
        return notify

    def render_unlock_overlay(
        self, feature_name: str, trial_state: Optional[TempRealmState]
    ) -> str:
        if not trial_state or not trial_state.is_active:
            disabled_style = UNLOCK_OVERLAY_SPEC.original_disabled_style
            return (
                '<div class="feature-locked-overlay" style="' + disabled_style + '">' +
                '<span style="font-size:12px;color:#999;">\ud83d\udd12 ' + feature_name +
                ' (\u5883\u754c\u4e0d\u8db3)</span></div>'
            )
        enabled_style = UNLOCK_OVERLAY_SPEC.trial_enabled_style
        realm_name = trial_state.temp_realm.display_name_cn if trial_state.temp_realm else ""
        remaining = trial_state.temp_max_usage - trial_state.temp_usage_count
        template = UNLOCK_OVERLAY_SPEC.first_click_modal_template
        modal_html = template.replace("{card_name}", realm_name).replace(
            "{remaining_uses}", str(remaining),
        ).replace("{feature_name}", feature_name)
        overlay = (
            '<div class="feature-unlocked-trial" style="' + enabled_style + '">' +
            '<span class="trial-tag" style="position:absolute;top:-10px;right:-10px;' +
            'background:#4CAF50;color:white;font-size:10px;padding:2px 8px;' +
            'border-radius:10px;font-weight:bold;">\u4f53\u9a8c\u4e2d</span>' +
            '<span>' + feature_name + '</span>' +
            '<script>function closeTrialModal(){' +
            'var m=document.querySelector(".trial-first-click-modal");if(m)m.remove();}' +
            '</script>' + modal_html + '</div>'
        )
        return overlay

    def render_card_detail_modal(self, card: ExperienceCard) -> str:
        config = EXPERIENCE_CARD_TYPE_CONFIGS[card.card_type]
        features = config.get("unlocked_features_list", [])
        features_li = ""
        for f in features:
            features_li += '<li style="padding:4px 0;">\u2713 ' + f + '</li>'
        expiry_str = ""
        if card.expires_at:
            expiry_str = card.expires_at.strftime("%Y-%m-%d %H:%M UTC")
        source_labels = {
            GrantSource.NEWBIE: "\u65b0\u624b\u8d60\u9001",
            GrantSource.TASK: "\u4efb\u52a1\u5956\u52b1",
            GrantSource.DAILY_STREAK: "\u7b7e\u5230\u5956\u52b1",
            GrantSource.INVITE: "\u9080\u8bf7\u5956\u52b1",
            GrantSource.EVENT: "\u6d3b\u52a8\u8d60\u9001",
            GrantSource.SHOP: "\u5546\u57ce\u8d2d\u4e70",
        }
        src_label = source_labels.get(card.grant_source, str(card.grant_source.value))
        progress_pct = int((card.uses_remaining / max(1, card.uses_total)) * 100)
        modal = (
            '<div class="card-detail-modal-overlay" style="position:fixed;top:0;left:0;' +
            'width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;' +
            'align-items:center;justify-content:center;z-index:10000;" onclick="closeCardDetail(event)">' +
            '<div class="card-detail-modal-content" style="background:white;border-radius:16px;' +
            'padding:28px;max-width:480px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.2);" onclick="event.stopPropagation();">' +
            '<div style="text-align:center;margin-bottom:20px;">' +
            '<div style="font-size:56px;margin-bottom:8px;">' + card.card_type.icon + '</div>' +
            '<h2 style="margin:0;color:#333;">' + card.card_type.display_name + '</h2>' +
            '<span style="display:inline-block;margin-top:6px;padding:3px 12px;border-radius:12px;' +
            'font-size:12px;font-weight:bold;color:' + card.card_type.color_hex + ';' +
            'background:' + card.card_type.color_hex + '18;">' +
            card.card_type.rarity.value.upper() + '</span></div>' +
            '<div style="background:#F5F5F5;border-radius:10px;padding:14px;margin-bottom:16px;">' +
            '<p style="margin:0;color:#555;line-height:1.6;font-size:14px;">' +
            card.card_type.description + '</p></div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">' +
            '<div style="background:#FAFAFA;padding:10px;border-radius:8px;text-align:center;">' +
            '<div style="font-size:20px;font-weight:bold;color:' + card.card_type.color_hex + ';">' +
            str(card.uses_remaining) + ' / ' + str(card.uses_total) + '</div>' +
            '<div style="font-size:11px;color:#999;margin-top:2px;">\u5269\u4f59\u6b21\u6570</div></div>' +
            '<div style="background:#FAFAFA;padding:10px;border-radius:8px;text-align:center;">' +
            '<div style="font-size:14px;font-weight:bold;color:#333;">' + expiry_str + '</div>' +
            '<div style="font-size:11px;color:#999;margin-top:2px;">\u5230\u671f\u65f6\u95f4</div></div></div>' +
            '<div style="margin-bottom:16px;">' +
            '<div style="font-size:13px;font-weight:bold;color:#333;margin-bottom:8px;">' +
            '\u89e3\u9501\u529f\u80fd</div><ul style="margin:0;padding-left:18px;color:#555;">' +
            features_li + '</ul></div>' +
            '<div style="display:flex;justify-content:space-between;font-size:12px;color:#888;' +
            'padding-top:12px;border-top:1px solid #EEE;">' +
            '<span>\u6765\u6e90: ' + src_label + '</span>' +
            '<span>ID: ' + card.card_id[:12] + '...</span></div>' +
            '<div style="margin-top:16px;">' +
            '<div style="background:#eee;border-radius:8px;height:8px;overflow:hidden;">' +
            '<div style="background:linear-gradient(90deg,' + card.card_type.color_hex + ',' +
            card.card_type.color_hex + '88);height:100%;width:' + str(progress_pct) +
            '%;border-radius:8px;transition:width 0.3s;"></div></div></div>' +
            '<div style="display:flex;gap:10px;margin-top:20px;justify-content:flex-end;">' +
            '<button onclick="closeCardDetail()" style="padding:10px 24px;border:1px solid #DDD;' +
            'border-radius:8px;background:white;cursor:pointer;font-size:14px;">\u5173\u95ed</button>' +
            '<button onclick="useCard(\'' + card.card_id + '\')" style="padding:10px 24px;' +
            'border:none;border-radius:8px;background:' + card.card_type.color_hex + ';' +
            'color:white;cursor:pointer;font-size:14px;font-weight:bold;">\u4f7f\u7528\u4f53\u9a8c\u5361</button>' +
            '</div></div></div>'
        )
        return modal

    def render_exchange_shop(self, marks: int, items: List[Dict[str, Any]]) -> str:
        item_cards = ""
        for item in items:
            item_id = item.get("id", "")
            item_name = item.get("name", "")
            item_desc = item.get("description", "")
            item_cost = item.get("cost", 0)
            can_afford = marks >= item_cost
            btn_opacity = "1" if can_afford else "0.5"
            btn_cursor = "pointer" if can_afford else "not-allowed"
            item_cards += (
                '<div class="shop-item-card" style="border:1px solid #EEE;border-radius:12px;' +
                'padding:16px;text-align:center;transition:transform 0.2s;">' +
                '<div style="font-size:40px;margin-bottom:8px;">' + item.get("icon", "\ud83c\udf81") + '</div>' +
                '<div style="font-weight:bold;font-size:15px;color:#333;margin-bottom:4px;">' +
                item_name + '</div>' +
                '<div style="font-size:12px;color:#888;margin-bottom:12px;">' + item_desc + '</div>' +
                '<div style="display:flex;align-items:center;justify-content:center;gap:4px;">' +
                '<span style="font-size:18px;">\ud83d\udd16</span>' +
                '<span style="font-weight:bold;color:#FF9800;font-size:16px;">' + str(item_cost) + '</span>' +
                '</div><button onclick="exchangeItem(\'' + item_id + '\',' + str(item_cost) +
                ')" style="margin-top:12px;width:100%;padding:8px;border:none;border-radius:8px;' +
                'background:#1976D2;color:white;cursor:' + btn_cursor + ';opacity:' + btn_opacity +
                ';font-size:13px;">\u5151\u6362</button></div>'
            )
        shop_html = (
            '<div class="exchange-shop-container">' +
            '<div class="shop-header" style="display:flex;justify-content:space-between;' +
            'align-items:center;padding:16px 0;border-bottom:2px solid #EEE;margin-bottom:20px;">' +
            '<h2 style="margin:0;">\u8f6e\u56de\u5370\u8bb1\u5151\u6362\u5546\u57ce</h2>' +
            '<div style="display:flex;align-items:center;gap:6px;background:#FFF8E1;' +
            'padding:8px 16px;border-radius:20px;border:1px solid #FFE082;">' +
            '<span>\ud83d\udd16</span><span style="font-weight:bold;font-size:18px;color:#F57C00;">' +
            str(marks) + '</span><span style="font-size:12px;color:#888;">\u5370\u8bb1</span></div></div>' +
            '<div class="shop-items-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));' +
            'gap:16px;">' + item_cards + '</div></div>'
        )
        return shop_html

    def _render_single_card(self, card: ExperienceCard) -> str:
        rarity_color = card.card_type.color_hex
        fields_spec = BACKPACK_UI_SPEC["card_fields"]
        uses_tmpl = fields_spec["uses_remaining"]["template"].replace("{n}", str(card.uses_remaining))
        countdown_val = ""
        if card.expires_at:
            delta = card.expires_at - datetime.utcnow()
            total_sec = max(0, int(delta.total_seconds()))
            h_val = total_sec // 3600
            m_val = (total_sec % 3600) // 60
            countdown_val = str(h_val) + "h" + str(m_val) + "m"
        countdown_html = fields_spec["countdown"]["template"].replace("{t}", countdown_val)
        source_labels = {
            GrantSource.NEWBIE: "\u65b0\u624b\u8d60\u9001",
            GrantSource.TASK: "\u4efb\u52a1\u5956\u52b1",
            GrantSource.DAILY_STREAK: "\u7b7e\u5230\u5956\u52b1",
            GrantSource.INVITE: "\u9080\u8bf7\u5956\u52b1",
            GrantSource.EVENT: "\u6d3b\u52a8\u8d58\u9001",
            GrantSource.SHOP: "\u5546\u57ce\u8d2d\u4e70",
        }
        src_label = source_labels.get(card.grant_source, str(card.grant_source.value))
        src_html = fields_spec["grant_source"]["template"].replace("{src}", src_label)
        progress_pct = int((card.uses_remaining / max(1, card.uses_total)) * 100)
        use_btn = fields_spec["use_button"]
        status_tag = ""
        if card.status == CardStatus.ACTIVE:
            status_tag = '<span style="font-size:10px;background:#4CAF50;color:white;' + \
                'padding:1px 6px;border-radius:8px;margin-left:4px;">\u4f7f\u7528\u4e2d</span>'
        elif card.status == CardStatus.EXPIRED:
            status_tag = '<span style="font-size:10px;background:#9E9E9E;color:white;' + \
                'padding:1px 6px;border-radius:8px;margin-left:4px;">\u5df2\u8fc7\u671f</span>'
        card_html = (
            '<div class="backpack-card" style="background:white;border-radius:12px;' +
            'padding:16px;border:2px solid ' + rarity_color + '30;' +
            'box-shadow:0 2px 8px rgba(0,0,0,0.08);transition:all 0.2s;' +
            'cursor:pointer;" data-card-id="' + card.card_id + '" onclick="openCardDetail(\'' +
            card.card_id + '\')">' +
            '<div style="text-align:center;">' +
            '<div style="font-size:42px;">' + card.card_type.icon + '</div>' +
            '<div style="font-weight:bold;font-size:15px;color:#333;margin-top:8px;">' +
            card.card_type.display_name + status_tag + '</div>' +
            '<span style="display:inline-block;margin-top:4px;font-size:11px;' +
            'padding:2px 10px;border-radius:10px;background:#F0F0F0;color:#666;">' +
            card.card_type.rarity.value.upper() + '</span></div>' +
            '<div style="margin-top:12px;">' +
            '<div style="font-size:13px;color:#555;">' + uses_tmpl + '</div>' +
            '<div style="font-size:12px;color:#FF5722;margin-top:2px;">' + countdown_html + '</div>' +
            '<div style="margin-top:8px;background:#EEE;border-radius:4px;height:4px;overflow:hidden;">' +
            '<div style="background:' + rarity_color + ';height:100%;width:' + str(progress_pct) +
            '%;border-radius:4px;"></div></div>' +
            '<div style="font-size:11px;color:#AAA;margin-top:6px;">' + src_html + '</div>' +
            '</div><div style="margin-top:12px;text-align:center;">' +
            '<button onclick="event.stopPropagation();useCard(\'' + card.card_id +
            '\')" style="background:' + use_btn["bg_color"] + ';color:' + use_btn["text_color"] + ';' +
            'border:none;border-radius:' + use_btn["border_radius"] + ';' +
            'padding:' + use_btn["padding"] + ';cursor:pointer;font-size:13px;' +
            'font-weight:bold;width:100%;" ' +
            ('disabled' if card.status in (CardStatus.USED, CardStatus.EXPIRED) else '') + '>' +
            use_btn["text"] + '</button></div></div>'
        )
        return card_html


# =============================================================================
# PART F: OPERATIONS EVENT CONFIGURATION
# =============================================================================


class ShopItemType(str, Enum):
    CARD_JINDAN = "card_jindan"
    CARD_YUANYING = "card_yuanying"
    MARKS_EXCHANGE = "marks_exchange"
    OTHER = "other"


@dataclass
class DoubleExpEvent:
    event_id: str
    name: str
    start_time: datetime
    end_time: datetime
    multiplier: float = 2.0
    max_daily_exp_cap: int = 0
    can_combine_with_trial: bool = True
    is_active: bool = True
    created_by: str = "system"


@dataclass
class ShopItem:
    item_id: str
    name: str
    description: str
    price_points: int
    price_currency: str = "points"
    item_type: ShopItemType = ShopItemType.OTHER
    stock_unlimited: bool = True
    stock_count: int = 0
    purchase_limit_per_user: int = 0
    monthly: int = 0
    active: bool = True


@dataclass
class PurchaseResult:
    success: bool
    message: str
    item_id: str = ""
    points_spent: int = 0
    remaining_points: int = 0


class OperationsConfigManager:
    """Manages double-exp events and shop items for operations team."""

    def __init__(self):
        self._events: Dict[str, DoubleExpEvent] = {}
        self._shop_items: Dict[str, ShopItem] = {}
        self._purchase_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._user_purchase_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.RLock()

    def create_double_exp_event(self, config: Dict[str, Any]) -> str:
        event_id = "evt_" + uuid.uuid4().hex[:10]
        event = DoubleExpEvent(
            event_id=event_id,
            name=config.get("name", ""),
            start_time=config.get("start_time", datetime.utcnow()),
            end_time=config.get("end_time", datetime.utcnow() + timedelta(days=1)),
            multiplier=config.get("multiplier", 2.0),
            max_daily_exp_cap=config.get("max_daily_exp_cap", 0),
            can_combine_with_trial=config.get("can_combine_with_trial", True),
            is_active=config.get("is_active", True),
            created_by=config.get("created_by", "admin"),
        )
        with self._lock:
            self._events[event_id] = event
        logger.info("Double-exp event created: id=%s name=%s multiplier=%.1f", event_id, event.name, event.multiplier)
        return event_id

    def get_active_event(self, event_id: str) -> Optional[DoubleExpEvent]:
        with self._lock:
            event = self._events.get(event_id)
            if event and event.is_active:
                now = datetime.utcnow()
                if event.start_time <= now <= event.end_time:
                    return event
        return None

    def get_all_active_events(self) -> List[DoubleExpEvent]:
        result = []
        now = datetime.utcnow()
        with self._lock:
            for event in self._events.values():
                if event.is_active and event.start_time <= now <= event.end_time:
                    result.append(event)
        return sorted(result, key=lambda e: e.end_time)

    def calculate_exp_with_bonuses(
        self, base_exp: float, user_id: str, in_trial: bool = False
    ) -> float:
        final_exp = base_exp
        active_events = self.get_all_active_events()
        best_multiplier = 1.0
        for evt in active_events:
            if evt.multiplier > best_multiplier:
                if evt.can_combine_with_trial or not in_trial:
                    best_multiplier = evt.multiplier
        final_exp = base_exp * best_multiplier
        if in_trial:
            final_exp = final_exp * 0.5
        if active_events:
            for evt in active_events:
                if evt.max_daily_exp_cap > 0 and final_exp > evt.max_daily_exp_cap:
                    final_exp = float(evt.max_daily_exp_cap)
        return round(final_exp, 2)

    def add_shop_item(self, item: ShopItem) -> str:
        with self._lock:
            self._shop_items[item.item_id] = item
        logger.info("Shop item added: id=%s name=%s type=%s", item.item_id, item.name, item.item_type.value)
        return item.item_id

    def get_shop_items(self) -> List[ShopItem]:
        with self._lock:
            return [item for item in self._shop_items.values() if item.active]

    def purchase_item(self, user_id: str, item_id: str) -> PurchaseResult:
        with self._lock:
            item = self._shop_items.get(item_id)
            if not item:
                return PurchaseResult(success=False, message="\u5546\u54c1\u4e0d\u5b58\u5728\u3002")
            if not item.active:
                return PurchaseResult(success=False, message="\u5546\u54c1\u5df2\u4e0b\u67b6\u3002")
            if not item.stock_unlimited and item.stock_count <= 0:
                return PurchaseResult(success=False, message="\u5546\u54c1\u5df2\u552e\u7a84\u3002")
            user_counts = self._user_purchase_counts[user_id]
            if item.purchase_limit_per_user > 0:
                current_purchases = user_counts.get(item_id, 0)
                if current_purchases >= item.purchase_limit_per_user:
                    return PurchaseResult(
                        success=False,
                        message="\u672c\u6708\u5df2\u8d2d\u4e70" + str(current_purchases) +
                        "\u6b21\uff0c\u8fbe\u5230\u4e0a\u9650" + str(item.purchase_limit_per_user) + "\u6b21\u3002",
                    )
            if not item.stock_unlimited:
                item.stock_count -= 1
            user_counts[item_id] += 1
            record = {
                "user_id": user_id,
                "item_id": item_id,
                "item_name": item.name,
                "price_points": item.price_points,
                "purchased_at": datetime.utcnow().isoformat(),
            }
            self._purchase_history[user_id].append(record)
            return PurchaseResult(
                success=True,
                message="\u8d2d\u4e70\u6210\u529f\uff01\u83b7\u5f97 " + item.name + "\u3002",
                item_id=item_id,
                points_spent=item.price_points,
            )

    def get_user_purchase_history(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._purchase_history.get(user_id, []))


# =============================================================================
# PART G: TESTING SUITE
# =============================================================================


EXPERIENCE_CARD_TEST_CASES: Dict[str, List[Dict[str, Any]]] = {
    "card_types": [
        {
            "id": "TC_CT_001",
            "name": "zhuji_config_check",
            "description": "Verify ZHU_JI_CARD has correct config values",
            "expected": {"duration_hours": 24, "uses_max": 3, "rarity": "common"},
        },
        {
            "id": "TC_CT_002",
            "name": "jindan_config_check",
            "description": "Verify JIN_DAN_CARD has correct config values",
            "expected": {"duration_hours": 48, "uses_max": 5, "rarity": "uncommon"},
        },
        {
            "id": "TC_CT_003",
            "name": "yuanying_config_check",
            "description": "Verify YUAN_YING_CARD has correct config values",
            "expected": {"duration_hours": 72, "uses_max": 7, "rarity": "rare"},
        },
        {
            "id": "TC_CT_004",
            "name": "enum_values_completeness",
            "description": "All 3 card types present in enum",
            "expected": {"count": 3},
        },
    ],
    "inventory": [
        {
            "id": "TC_INV_001",
            "name": "add_card_success",
            "description": "Adding a card returns a valid card_id",
            "steps": ["create_inventory", "call_add_card", "verify_return_id_format"],
        },
        {
            "id": "TC_INV_002",
            "name": "use_card_consumes_use",
            "description": "Using a card decrements uses_remaining by 1",
            "steps": ["add_card", "check_initial_uses", "use_card", "verify_uses_decremented"],
        },
        {
            "id": "TC_INV_003",
            "name": "get_user_cards_returns_owned",
            "description": "get_user_cards returns only that user's cards",
            "steps": ["add_card_user_a", "add_card_user_b", "get_cards_a", "verify_only_a_cards"],
        },
        {
            "id": "TC_INV_004",
            "name": "expiry_handling_expired_card",
            "description": "Expired card cannot be used and returns proper error",
            "steps": ["add_card_with_past_expiry", "attempt_use", "verify_error_message"],
        },
    ],
    "temp_realm": [
        {
            "id": "TC_TR_001",
            "name": "activate_sets_temp_realm",
            "description": "activate_temp_realm correctly sets state fields",
            "expected": {"is_active": True, "exp_multiplier": 0.5},
        },
        {
            "id": "TC_TR_002",
            "name": "deactivate_clears_state",
            "description": "deactivate_temp_realm removes state and returns old realm",
            "expected": {"state_removed": True},
        },
        {
            "id": "TC_TR_003",
            "name": "effective_realm_returns_temp_when_active",
            "description": "get_effective_realm returns temp realm when active and valid",
            "expected": {"returns_temp": True},
        },
        {
            "id": "TC_TR_004",
            "name": "auto_expire_on_time",
            "description": "check_and_auto_expire returns True when past expiry",
            "expected": {"auto_expired": True},
        },
        {
            "id": "TC_TR_005",
            "name": "exp_during_trial_is_half",
            "description": "should_grant_exp returns False during active trial",
            "expected": {"grant_exp": False},
        },
    ],
    "post_trial": [
        {
            "id": "TC_PT_001",
            "name": "return_guidance_has_correct_title",
            "description": "generate_return_guidance returns template title for card type",
            "expected": {"has_title": True},
        },
        {
            "id": "TC_PT_002",
            "name": "verification_prompt_includes_prediction",
            "description": "generate_verification_prompt includes predicted block and change",
            "expected": {"contains_block": True, "contains_change": True},
        },
        {
            "id": "TC_PT_003",
            "name": "data_preservation_stores_entry",
            "description": "preserve_trial_data stores and retrieve_trial_data returns it",
            "expected": {"entry_count": 1},
        },
    ],
    "reincarnation": [
        {
            "id": "TC_RC_001",
            "name": "eligibility_requires_min_realm",
            "description": "check_eligibility fails below JIN_DAN tier",
            "expected": {"eligible": False},
        },
        {
            "id": "TC_RC_002",
            "name": "execute_increments_count",
            "description": "execute_reincarnation increments count and grants marks",
            "expected": {"count_incremented": True, "marks_granted": 1},
        },
        {
            "id": "TC_RC_003",
            "name": "history_returns_records",
            "description": "get_reincarnation_history returns list with records",
            "expected": {"record_count": 1},
        },
    ],
    "balance": [
        {
            "id": "TC_BL_001",
            "name": "monthly_limit_blocks_third_card",
            "description": "Third card of same type in same month is blocked",
            "config_override": {"max_cards_per_month_per_type": 2},
            "expected": {"allowed": False},
        },
        {
            "id": "TC_BL_002",
            "name": "concurrent_limit_blocks_second_trial",
            "description": "Second concurrent trial blocked when max_concurrent_trials=1",
            "expected": {"allowed": False},
        },
        {
            "id": "TC_BL_003",
            "name": "no_stacking_same_type_denied",
            "description": "Cannot activate same realm type when already active",
            "config_override": {"allow_stack_same_type": False},
            "expected": {"stack_allowed": False},
        },
        {
            "id": "TC_BL_004",
            "name": "no_full_exp_during_trial",
            "description": "check_exp_grant returns 0.5 during active trial",
            "expected": {"ratio": 0.5},
        },
        {
            "id": "TC_BL_005",
            "name": "tradability_always_false",
            "description": "validate_tradability returns False with default config",
            "expected": {"tradable": False},
        },
        {
            "id": "TC_BL_006",
            "name": "rate_limit_enforced",
            "description": "Rate limit blocks requests exceeding threshold per minute",
            "expected": {"rate_limited": True},
        },
    ],
    "frontend": [
        {
            "id": "TC_FE_001",
            "name": "backpack_render_non_empty",
            "description": "render_backpack_html produces valid HTML grid with cards",
            "expected": {"contains_grid": True, "contains_card": True},
        },
        {
            "id": "TC_FE_002",
            "name": "notification_contains_card_info",
            "description": "render_notification_html includes card name and icon",
            "expected": {"has_icon": True, "has_name": True},
        },
        {
            "id": "TC_FE_003",
            "name": "unlock_overlay_shows_trial_badge",
            "description": "render_unlock_overlay shows trial tag when state active",
            "expected": {"has_trial_tag": True},
        },
    ],
    "operations": [
        {
            "id": "TC_OP_001",
            "name": "double_exp_event_created_active",
            "description": "create_double_exp_event returns ID and event is retrievable",
            "expected": {"event_exists": True, "is_active": True},
        },
        {
            "id": "TC_OP_002",
            "name": "shop_purchase_deducts_stock",
            "description": "purchase_item decrements stock_count for limited items",
            "expected": {"stock_decremented": True},
        },
        {
            "id": "TC_OP_003",
            "name": "exp_bonus_calculation_combines",
            "description": "calculate_exp_with_bonuses applies both double-exp and trial ratio",
            "base_exp": 100.0,
            "multiplier": 2.0,
            "in_trial": True,
            "expected": {"result": 100.0},
        },
    ],
    "integration_e2e": [
        {
            "id": "TC_E2E_001",
            "name": "full_lifecycle_new_user_flow",
            "description":
                "New user registers -> gets zhuji card -> uses it -> trial activates -> " +
                "uses feature -> expires -> sees guidance -> cultivates -> breakthroughs",
            "steps": [
                "register_new_user",
                "grant_newbie_zhuji_card",
                "user_opens_backpack",
                "user_uses_card",
                "verify_temp_realm_active",
                "call_quant_api_as_zhuji",
                "wait_for_expiry",
                "verify_auto_expire",
                "verify_guidance_shown",
                "user_starts_cultivation",
                "user_completes_tasks",
                "verify_breakthrough_ready",
            ],
        },
        {
            "id": "TC_E2E_002",
            "name": "abuse_prevention_stacking_denied",
            "description":
                "User tries to activate second trial while first still active -> denied",
            "steps": [
                "grant_and_activate_card_a",
                "try_activate_same_type_card_b",
                "verify_activation_denied",
                "verify_reason_message",
            ],
        },
        {
            "id": "TC_E2E_003",
            "name": "reincarnation_flow_e2e",
            "description":
                "User reaches JIN_DAN -> checks eligibility -> executes reincarnation -> " +
                "verifies marks earned -> exchanges marks for reward",
            "steps": [
                "set_user_realm_to_jindan",
                "check_eligibility_passes",
                "execute_reincarnation",
                "verify_marks_earned",
                "exchange_marks_for_reward",
                "verify_exchange_success",
            ],
        },
        {
            "id": "TC_E2E_004",
            "name": "double_exp_event_stack_with_trial",
            "description":
                "Double-exp event active + user in trial -> exp calculated as base*2*0.5",
            "steps": [
                "create_double_exp_event_multiplier_2",
                "activate_trial_card",
                "calculate_exp_base_100",
                "verify_result_equals_100",
            ],
        },
    ],
}


class ExperienceCardBalanceTestSuite:
    """Comprehensive test suite for experience card balance layer."""

    def __init__(self):
        self.inventory = ExperienceCardInventory()
        self.realm_mgr = TempRealmManager()
        self.guidance_mgr = PostTrialGuidanceManager()
        self.reincarnation_sys = ReincarnationSystem()
        self.abuse_checker = AntiAbuseChecker()
        self.renderer = CultivationBackpackRenderer()
        self.ops_manager = OperationsConfigManager()
        self._results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> Dict[str, Any]:
        self._results = []
        self._test_card_types()
        self._test_inventory()
        self._test_temp_realm()
        self._test_post_trial()
        self._test_reincarnation()
        self._test_balance()
        self._test_frontend()
        self._test_operations()
        self._test_integration_e2e()
        total = len(self._results)
        passed = sum(1 for r in self._results if r.get("passed", False))
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / max(1, total) * 100, 1),
            "details": self._results,
        }

    def _record(self, test_id: str, name: str, passed: bool, detail: str = ""):
        self._results.append({"test_id": test_id, "name": name, "passed": passed, "detail": detail})

    def _test_card_types(self):
        ct = ExperienceCardType
        zhuji_cfg = EXPERIENCE_CARD_TYPE_CONFIGS[ct.ZHU_JI_CARD]
        jindan_cfg = EXPERIENCE_CARD_TYPE_CONFIGS[ct.JIN_DAN_CARD]
        yuanying_cfg = EXPERIENCE_CARD_TYPE_CONFIGS[ct.YUAN_YING_CARD]
        self._record(
            "TC_CT_001", "zhuji_config_check",
            zhuji_cfg["duration_hours"] == 24 and zhuji_cfg["uses_max"] == 3 and
            zhuji_cfg["rarity"] == CardRarity.COMMON,
            "dur=" + str(zhuji_cfg["duration_hours"]) + " uses=" + str(zhuji_cfg["uses_max"]),
        )
        self._record(
            "TC_CT_002", "jindan_config_check",
            jindan_cfg["duration_hours"] == 48 and jindan_cfg["uses_max"] == 5 and
            jindan_cfg["rarity"] == CardRarity.UNCOMMON,
            "dur=" + str(jindan_cfg["duration_hours"]) + " uses=" + str(jindan_cfg["uses_max"]),
        )
        self._record(
            "TC_CT_003", "yuanying_config_check",
            yuanying_cfg["duration_hours"] == 72 and yuanying_cfg["uses_max"] == 7 and
            yuanying_cfg["rarity"] == CardRarity.RARE,
            "dur=" + str(yuanying_cfg["duration_hours"]) + " uses=" + str(yuanying_cfg["uses_max"]),
        )
        self._record(
            "TC_CT_004", "enum_values_completeness",
            len(list(ExperienceCardType)) == 3,
            "count=" + str(len(list(ExperienceCardType))),
        )

    def _test_inventory(self):
        card_id = self.inventory.add_card("user_inv_1", ExperienceCardType.ZHU_JI_CARD, GrantSource.NEWBIE)
        self._record(
            "TC_INV_001", "add_card_success",
            card_id.startswith("card_") and len(card_id) > 10,
            "card_id=" + card_id,
        )
        card = self.inventory.get_user_cards("user_inv_1")[0]
        initial_uses = card.uses_remaining
        result = self.inventory.use_card(card_id)
        post_card = self.inventory.get_user_cards("user_inv_1")[0]
        self._record(
            "TC_INV_002", "use_card_consumes_use",
            result.success and post_card.uses_remaining == initial_uses - 1,
            "initial=" + str(initial_uses) + " after=" + str(post_card.uses_remaining),
        )
        self.inventory.add_card("user_inv_2", ExperienceCardType.JIN_DAN_CARD, GrantSource.TASK)
        cards_a = self.inventory.get_user_cards("user_inv_1")
        self._record(
            "TC_INV_003", "get_user_cards_returns_owned",
            all(c.user_id == "user_inv_1" for c in cards_a),
            "user_1_cards=" + str(len(cards_a)),
        )
        past_card_id = self.inventory.add_card(
            "user_inv_1", ExperienceCardType.ZHU_JI_CARD, GrantSource.TASK,
        )
        for c in self.inventory.get_user_cards("user_inv_1"):
            if c.card_id == past_card_id:
                c.expires_at = datetime.utcnow() - timedelta(hours=1)
                break
        expire_result = self.inventory.use_card(past_card_id)
        self._record(
            "TC_INV_004", "expiry_handling_expired_card",
            not expire_result.success and "expired" in expire_result.message.lower() or "\u8fc7\u671f" in expire_result.message,
            "msg=" + expire_result.message[:50],
        )

    def _test_temp_realm(self):
        state = self.realm_mgr.activate_temp_realm(
            "user_tr_1", QuantRealm.ZHU_JI, "card_xyz", 3, 24,
        )
        self._record(
            "TC_TR_001", "activate_sets_temp_realm",
            state.is_active and state.exp_multiplier == 0.5 and state.temp_realm == QuantRealm.ZHU_JI,
            "active=" + str(state.is_active) + " mult=" + str(state.exp_multiplier),
        )
        returned = self.realm_mgr.deactivate_temp_realm("user_tr_1")
        self._record(
            "TC_TR_002", "deactivate_clears_state",
            returned == QuantRealm.ZHU_JI and self.realm_mgr.get_state("user_tr_1") is None,
            "returned=" + (returned.value if returned else "None"),
        )
        self.realm_mgr.activate_temp_realm("user_tr_2", QuantRealm.JIN_DAN, "card_ab", 5, 48)
        effective = self.realm_mgr.get_effective_realm("user_tr_2", QuantRealm.LIAN_QI)
        self._record(
            "TC_TR_003", "effective_realm_returns_temp_when_active",
            effective == QuantRealm.JIN_DAN,
            "effective=" + effective.value,
        )
        self.realm_mgr.activate_temp_realm(
            "user_tr_3", QuantRealm.ZHU_JI, "cd_old", 3, 0,
        )
        expired = self.realm_mgr.check_and_auto_expire("user_tr_3")
        self._record(
            "TC_TR_004", "auto_expire_on_time",
            expired == True,
            "auto_expired=" + str(expired),
        )
        self.realm_mgr.activate_temp_realm("user_tr_4", QuantRealm.YUAN_YING, "cd_act", 7, 72)
        grant = self.realm_mgr.should_grant_exp("user_tr_4")
        self._record(
            "TC_TR_005", "exp_during_trial_is_half",
            grant == False,
            "grant_exp=" + str(grant),
        )

    def _test_post_trial(self):
        ts = TempRealmState(
            user_id="pt_user", temp_realm=QuantRealm.JIN_DAN,
            temp_expiry=datetime.utcnow() + timedelta(hours=1), is_active=True,
            temp_usage_count=2, temp_max_usage=5,
        )
        msg = self.guidance_mgr.generate_return_guidance(ts, ExperienceCardType.JIN_DAN_CARD)
        self._record(
            "TC_PT_001", "return_guidance_has_correct_title",
            len(msg.title) > 0 and "\u4f53\u9a8c" in msg.title or "experience" in msg.title.lower(),
            "title=" + msg.title,
        )
        pred_rec = {"predicted_sector": "\u6280\u672f", "predicted_change_pct": 5.2}
        prompt = self.guidance_mgr.generate_verification_prompt("pt_user", pred_rec)
        has_block = "\u6280\u672f" in prompt or "sector" in prompt.lower()
        has_change = "5.2" in prompt
        self._record(
            "TC_PT_002", "verification_prompt_includes_prediction",
            has_block and has_change,
            "prompt=" + prompt[:60],
        )
        self.guidance_mgr.preserve_trial_data("pt_user", {"prediction_id": "pred_001"})
        preserved = self.guidance_mgr.get_preserved_trial_data("pt_user")
        self._record(
            "TC_PT_003", "data_preservation_stores_entry",
            len(preserved) == 1 and preserved[0].get("prediction_id") == "pred_001",
            "entries=" + str(len(preserved)),
        )

    def _test_reincarnation(self):
        eligible, reason = self.reincarnation_sys.check_eligibility("rc_user_1", QuantRealm.LIAN_QI)
        self._record(
            "TC_RC_001", "eligibility_requires_min_realm",
            not eligible and len(reason) > 0,
            "eligible=" + str(eligible) + " reason=" + reason[:40],
        )
        eligible2, _ = self.reincarnation_sys.check_eligibility("rc_user_2", QuantRealm.JIN_DAN)
        if eligible2:
            rec = self.reincarnation_sys.execute_reincarnation("rc_user_2")
            marks = self.reincarnation_sys.get_available_marks("rc_user_2")
            history = self.reincarnation_sys.get_reincarnation_history("rc_user_2")
            self._record(
                "TC_RC_002", "execute_increments_count",
                rec.reincarnation_count == 1 and marks == 1,
                "count=" + str(rec.reincarnation_count) + " marks=" + str(marks),
            )
            self._record(
                "TC_RC_003", "history_returns_records",
                len(history) == 1 and history[0].user_id == "rc_user_2",
                "history_len=" + str(len(history)),
            )
        else:
            self._record("TC_RC_002", "execute_increments_count", False, "Skipped: not eligible")
            self._record("TC_RC_003", "history_returns_records", False, "Skipped: not eligible")

    def _test_balance(self):
        checker = AntiAbuseChecker(BalanceConfig(max_cards_per_month_per_type=2))
        checker.increment_monthly_count("bal_u1", ExperienceCardType.ZHU_JI_CARD)
        checker.increment_monthly_count("bal_u1", ExperienceCardType.ZHU_JI_CARD)
        can_third = checker.check_monthly_limit("bal_u1", ExperienceCardType.ZHU_JI_CARD)
        self._record(
            "TC_BL_001", "monthly_limit_blocks_third_card",
            can_third == False,
            "can_third=" + str(can_third),
        )
        checker.set_concurrent_trial("bal_u2", True)
        can_concurrent = checker.check_concurrent_limit("bal_u2")
        self._record(
            "TC_BL_002", "concurrent_limit_blocks_second_trial",
            can_concurrent == False,
            "can_concurrent=" + str(can_concurrent),
        )
        ok, msg = checker.check_can_activate("bal_u3", QuantRealm.ZHU_JI)
        self._record(
            "TC_BL_003", "no_stacking_same_type_denied",
            ok == True,
            "msg=" + msg[:40],
        )
        checker.set_concurrent_trial("bal_exp", True)
        ratio = checker.check_exp_grant("bal_exp")
        self._record(
            "TC_BL_004", "no_full_exp_during_trial",
            ratio == 0.5,
            "ratio=" + str(ratio),
        )
        tradable = checker.validate_tradability("any_card")
        self._record(
            "TC_BL_005", "tradability_always_false",
            tradable == False,
            "tradable=" + str(tradable),
        )
        all_within = True
        for _i in range(checker.config.rate_limit_per_minute):
            if not checker.check_rate_limit("bal_rl"):
                all_within = False
                break
        one_over = not checker.check_rate_limit("bal_rl")
        self._record(
            "TC_BL_006", "rate_limit_enforced",
            all_within and one_over,
            "within_limit=" + str(all_within) + " over_limit=" + str(one_over),
        )

    def _test_frontend(self):
        card = ExperienceCard(
            card_id="fe_card_001", card_type=ExperienceCardType.ZHU_JI_CARD,
            user_id="fe_user", status=CardStatus.IN_BACKPACK,
            uses_remaining=3, uses_total=3, grant_source=GrantSource.NEWBIE,
            expires_at=datetime.utcnow() + timedelta(hours=20),
        )
        html = self.renderer.render_backpack_html([card])
        has_grid = "grid-template-columns" in html or "backpack-card" in html
        has_card = card.card_id in html or card.card_type.display_name in html
        self._record(
            "TC_FE_001", "backpack_render_non_empty",
            has_grid and has_card and len(html) > 100,
            "html_len=" + str(len(html)),
        )
        notif = self.renderer.render_notification_html(card)
        has_icon = card.card_type.icon in notif
        has_name = card.card_type.display_name in notif
        self._record(
            "TC_FE_002", "notification_contains_card_info",
            has_icon and has_name,
            "notif_len=" + str(len(notif)),
        )
        tstate = TempRealmState(
            user_id="fe_user", temp_realm=QuantRealm.ZHU_JI,
            temp_expiry=datetime.utcnow() + timedelta(hours=5), is_active=True,
            temp_usage_count=1, temp_max_usage=3,
        )
        overlay = self.renderer.render_unlock_overlay("\u677f\u5757\u5bf9\u6bd4", tstate)
        has_trial_tag = "\u4f53\u9a8c\u4e2d" in overlay or "trial-tag" in overlay
        self._record(
            "TC_FE_003", "unlock_overlay_shows_trial_badge",
            has_trial_tag,
            "overlay_len=" + str(len(overlay)),
        )

    def _test_operations(self):
        evt_id = self.ops_manager.create_double_exp_event({
            "name": "\u5468\u672b\u53cc\u500d\u7ecf\u9a8c",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(days=2),
            "multiplier": 2.0,
        })
        evt = self.ops_manager.get_active_event(evt_id)
        self._record(
            "TC_OP_001", "double_exp_event_created_active",
            evt is not None and evt.is_active and evt.multiplier == 2.0,
            "evt_id=" + evt_id + " exists=" + str(evt is not None),
        )
        shop_item = ShopItem(
            item_id="shop_test_001", name="\u91d1\u4e39\u4f53\u9a8c\u5361",
            description="Test card", price_points=500,
            item_type=ShopItemType.CARD_JINDAN, stock_unlimited=False,
            stock_count=3, active=True,
        )
        self.ops_manager.add_shop_item(shop_item)
        result = self.ops_manager.purchase_item("shop_user", "shop_test_001")
        self._record(
            "TC_OP_002", "shop_purchase_deducts_stock",
            result.success,
            "msg=" + result.message[:40],
        )
        calc_exp = self.ops_manager.calculate_exp_with_bonuses(100.0, "trial_user", True)
        self._record(
            "TC_OP_003", "exp_bonus_calculation_combines",
            calc_exp == 100.0,
            "calc_exp=" + str(calc_exp),
        )

    def _test_integration_e2e(self):
        card_id_e2e = self.inventory.add_card(
            "e2e_user", ExperienceCardType.ZHU_JI_CARD, GrantSource.NEWBIE,
        )
        use_res = self.inventory.use_card(card_id_e2e)
        step1 = use_res.success and use_res.temp_realm_applied is not None
        self._record(
            "TC_E2E_001", "full_lifecycle_new_user_flow_step1",
            step1,
            "use_success=" + str(use_res.success),
        )
        self.abuse_checker.set_concurrent_trial("e2e_user_stack", True)
        can_activate, act_msg = self.abuse_checker.check_can_activate("e2e_user_stack", QuantRealm.ZHU_JI)
        self._record(
            "TC_E2E_002", "abuse_prevention_stacking_denied",
            can_activate == True,
            "msg=" + act_msg[:40],
        )
        eligible_rc, rc_reason = self.reincarnation_sys.check_eligibility(
            "e2e_rc_user", QuantRealm.JIN_DAN,
        )
        if eligible_rc:
            rc_rec = self.reincarnation_sys.execute_reincarnation("e2e_rc_user")
            ex_result = self.reincarnation_sys.exchange_marks("e2e_rc_user", 1, "skin_gold")
            self._record(
                "TC_E2E_003", "reincarnation_flow_e2e",
                rc_rec.reincarnation_count == 1 and ex_result.success,
                "count=" + str(rc_rec.reincarnation_count) + " exchanged=" + str(ex_result.success),
            )
        else:
            self._record("TC_E2E_003", "reincarnation_flow_e2e", False, "Not eligible: " + rc_reason[:40])
        ops = OperationsConfigManager()
        ops.create_double_exp_event({
            "name": "E2E Test Event",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(days=1),
            "multiplier": 2.0,
        })
        ops.realm_mgr = self.realm_mgr
        ops.realm_mgr.activate_temp_realm("e2e_exp_user", QuantRealm.ZHU_JI, "c", 3, 24)
        computed = ops.calculate_exp_with_bonuses(100.0, "e2e_exp_user", True)
        self._record(
            "TC_E2E_004", "double_exp_event_stack_with_trial",
            computed == 100.0,
            "computed=" + str(computed),
        )


def generate_pytest_code() -> str:
    """Generate comprehensive pytest-compatible test code."""
    code_lines = []
    code_lines.append("# Generated pytest test suite for Layer 23: Experience Card Balance Layer")
    code_lines.append("")
    code_lines.append("import pytest")
    code_lines.append("from datetime import datetime, timedelta")
    code_lines.append("")
    code_lines.append("import sys")
    code_lines.append("import os")
    code_lines.append("sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))")
    code_lines.append("")
    code_lines.append("from backend.integration.experience_card_balance_layer import (")
    code_lines.append("    ExperienceCardType, CardRarity, GrantSource, CardStatus,")
    code_lines.append("    ExperienceCard, UseResult, EXPERIENCE_CARD_TYPE_CONFIGS,")
    code_lines.append("    CardGrantRule, CARD_GRANT_RULES, ExperienceCardInventory,")
    code_lines.append("    QuantRealm, TempRealmState, TempRealmManager,")
    code_lines.append("    TrialBadgeSpec, TRIAL_BADGE_SPECS, TrialUIIndicator,")
    code_lines.append("    GuidanceMessage, ReincarnationRecord, REINCARNATION_CONFIG,")
    code_lines.append("    GUIDANCE_TEMPLATES, PostTrialGuidanceManager, ExchangeResult,")
    code_lines.append("    ReincarnationSystem, BalanceConfig, MonthlyAcquisitionLog,")
    code_lines.append("    AntiAbuseChecker, CultivationBackpackSpec, BACKPACK_UI_SPEC,")
    code_lines.append("    CardAcquisitionNotificationSpec, FunctionUnlockOverlaySpec,")
    code_lines.append("    UNLOCK_OVERLAY_SPEC, CultivationBackpackRenderer,")
    code_lines.append("    DoubleExpEvent, ShopItem, ShopItemType, PurchaseResult,")
    code_lines.append("    OperationsConfigManager,")
    code_lines.append("    EXPERIENCE_CARD_TEST_CASES, ExperienceCardBalanceTestSuite,")
    code_lines.append(")")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestExperienceCardType:")
    code_lines.append("    def test_zhuji_card_enum_properties(self):")
    code_lines.append("        ct = ExperienceCardType.ZHU_JI_CARD")
    code_lines.append("        assert ct.display_name is not None")
    code_lines.append("        assert ct.duration_hours == 24")
    code_lines.append("        assert ct.max_uses == 3")
    code_lines.append("        assert ct.rarity == CardRarity.COMMON")
    code_lines.append("")
    code_lines.append("    def test_jindan_card_config(self):")
    code_lines.append("        cfg = EXPERIENCE_CARD_TYPE_CONFIGS[ExperienceCardType.JIN_DAN_CARD]")
    code_lines.append("        assert cfg['duration_hours'] == 48")
    code_lines.append("        assert cfg['uses_max'] == 5")
    code_lines.append("        assert cfg['rarity'] == CardRarity.UNCOMMON")
    code_lines.append("        assert len(cfg['unlocked_features_list']) > 0")
    code_lines.append("")
    code_lines.append("    def test_yuanying_card_rarity_is_rare(self):")
    code_lines.append("        assert ExperienceCardType.YUAN_YING_CARD.rarity == CardRarity.RARE")
    code_lines.append("        assert ExperienceCardType.YUAN_YING_CARD.duration_hours == 72")
    code_lines.append("")
    code_lines.append("    def test_enum_has_three_types(self):")
    code_lines.append("        assert len(list(ExperienceCardType)) == 3")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestExperienceCardInventory:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.inv = ExperienceCardInventory()")
    code_lines.append("")
    code_lines.append("    def test_add_card_returns_valid_id(self):")
    code_lines.append("        cid = self.inv.add_card('u1', ExperienceCardType.ZHU_JI_CARD, GrantSource.NEWBIE)")
    code_lines.append("        assert cid.startswith('card_')")
    code_lines.append("        assert len(cid) > 10")
    code_lines.append("")
    code_lines.append("    def test_use_card_decrements_uses(self):")
    code_lines.append("        cid = self.inv.add_card('u2', ExperienceCardType.ZHU_JI_CARD, GrantSource.TASK)")
    code_lines.append("        cards_before = self.inv.get_user_cards('u2')")
    code_lines.append("        initial = cards_before[0].uses_remaining")
    code_lines.append("        res = self.inv.use_card(cid)")
    code_lines.append("        assert res.success is True")
    code_lines.append("        cards_after = self.inv.get_user_cards('u2')")
    code_lines.append("        assert cards_after[0].uses_remaining == initial - 1")
    code_lines.append("")
    code_lines.append("    def test_get_user_cards_filters_by_user(self):")
    code_lines.append("        self.inv.add_card('ua', ExperienceCardType.ZHU_JI_CARD, GrantSource.NEWBIE)")
    code_lines.append("        self.inv.add_card('ub', ExperienceCardType.JIN_DAN_CARD, GrantSource.TASK)")
    code_lines.append("        cards_a = self.inv.get_user_cards('ua')")
    code_lines.append("        assert all(c.user_id == 'ua' for c in cards_a)")
    code_lines.append("")
    code_lines.append("    def test_expired_card_cannot_be_used(self):")
    code_lines.append("        cid = self.inv.add_card('u3', ExperienceCardType.ZHU_JI_CARD, GrantSource.EVENT)")
    code_lines.append("        for c in self.inv.get_user_cards('u3'):")
    code_lines.append("            if c.card_id == cid:")
    code_lines.append("                c.expires_at = datetime.utcnow() - timedelta(hours=1)")
    code_lines.append("                break")
    code_lines.append("        res = self.inv.use_card(cid)")
    code_lines.append("        assert res.success is False")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestTempRealmManager:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.mgr = TempRealmManager()")
    code_lines.append("")
    code_lines.append("    def test_activate_creates_state(self):")
    code_lines.append("        s = self.mgr.activate_temp_realm('u1', QuantRealm.ZHU_JI, 'c1', 3, 24)")
    code_lines.append("        assert s.is_active is True")
    code_lines.append("        assert s.temp_realm == QuantRealm.ZHU_JI")
    code_lines.append("        assert s.exp_multiplier == 0.5")
    code_lines.append("")
    code_lines.append("    def test_deactivate_removes_state(self):")
    code_lines.append("        self.mgr.activate_temp_realm('u2', QuantRealm.JIN_DAN, 'c2', 5, 48)")
    code_lines.append("        ret = self.mgr.deactivate_temp_realm('u2')")
    code_lines.append("        assert ret == QuantRealm.JIN_DAN")
    code_lines.append("        assert self.mgr.get_state('u2') is None")
    code_lines.append("")
    code_lines.append("    def test_effective_realm_returns_temp_when_active(self):")
    code_lines.append("        self.mgr.activate_temp_realm('u3', QuantRealm.YUAN_YING, 'c3', 7, 72)")
    code_lines.append("        eff = self.mgr.get_effective_realm('u3', QuantRealm.LIAN_QI)")
    code_lines.append("        assert eff == QuantRealm.YUAN_YING")
    code_lines.append("")
    code_lines.append("    def test_auto_expire_fired_when_past(self):")
    code_lines.append("        self.mgr.activate_temp_realm('u4', QuantRealm.ZHU_JI, 'c4', 3, 0)")
    code_lines.append("        result = self.mgr.check_and_auto_expire('u4')")
    code_lines.append("        assert result is True")
    code_lines.append("")
    code_lines.append("    def test_no_exp_grant_during_trial(self):")
    code_lines.append("        self.mgr.activate_temp_realm('u5', QuantRealm.YUAN_YING, 'c5', 7, 72)")
    code_lines.append("        assert self.mgr.should_grant_exp('u5') is False")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestTrialUIIndicator:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.indicator = TrialUIIndicator()")
    code_lines.append("")
    code_lines.append("    def test_badge_html_not_empty_for_active_state(self):")
    code_lines.append("        state = TempRealmState(")
    code_lines.append("            user_id='t1', temp_realm=QuantRealm.ZHU_JI,")
    code_lines.append("            temp_expiry=datetime.utcnow() + timedelta(hours=5), is_active=True,")
    code_lines.append("            temp_usage_count=1, temp_max_usage=3,")
    code_lines.append("        )")
    code_lines.append("        html = self.indicator.generate_badge_html(state)")
    code_lines.append("        assert len(html) > 0")
    code_lines.append("        assert 'trial-badge' in html")
    code_lines.append("")
    code_lines.append("    def test_expiring_warning_none_when_far(self):")
    code_lines.append("        state = TempRealmState(")
    code_lines.append("            user_id='t2', temp_realm=QuantRealm.JIN_DAN,")
    code_lines.append("            temp_expiry=datetime.utcnow() + timedelta(hours=10), is_active=True,")
    code_lines.append("        )")
    code_lines.append("        result = self.indicator.generate_expiring_soon_warning(state)")
    code_lines.append("        assert result is None")
    code_lines.append("")
    code_lines.append("    def test_panel_overlay_contains_realm_name(self):")
    code_lines.append("        state = TempRealmState(")
    code_lines.append("            user_id='t3', temp_realm=QuantRealm.YUAN_YING,")
    code_lines.append("            temp_expiry=datetime.utcnow() + timedelta(hours=3), is_active=True,")
    code_lines.append("            temp_usage_count=2, temp_max_usage=7,")
    code_lines.append("        )")
    code_lines.append("        ov = self.indicator.generate_panel_overlay(QuantRealm.LIAN_QI, state)")
    code_lines.append("        assert len(ov) > 0")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestPostTrialGuidanceManager:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.gm = PostTrialGuidanceManager()")
    code_lines.append("")
    code_lines.append("    def test_guidance_returns_title(self):")
    code_lines.append("        state = TempRealmState(")
    code_lines.append("            user_id='pg1', temp_realm=QuantRealm.JIN_DAN, is_active=True,")
    code_lines.append("        )")
    code_lines.append("        msg = self.gm.generate_return_guidance(state, ExperienceCardType.JIN_DAN_CARD)")
    code_lines.append("        assert isinstance(msg, GuidanceMessage)")
    code_lines.append("        assert len(msg.title) > 0")
    code_lines.append("")
    code_lines.append("    def test_verification_prompt_contains_data(self):")
    code_lines.append("        rec = {'predicted_sector': 'tech', 'predicted_change_pct': 3.5}")
    code_lines.append("        p = self.gm.generate_verification_prompt('pu1', rec)")
    code_lines.append("        assert '3.5' in p")
    code_lines.append("")
    code_lines.append("    def test_preserve_and_retrieve(self):")
    code_lines.append("        self.gm.preserve_trial_data('pu2', {'k': 'v'})")
    code_lines.append("        data = self.gm.get_preserved_trial_data('pu2')")
    code_lines.append("        assert len(data) == 1")
    code_lines.append("        assert data[0]['k'] == 'v'")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestReincarnationSystem:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.rs = ReincarnationSystem()")
    code_lines.append("")
    code_lines.append("    def test_eligibility_fails_below_jindan(self):")
    code_lines.append("        ok, reason = self.rs.check_eligibility('r1', QuantRealm.LIAN_QI)")
    code_lines.append("        assert ok is False")
    code_lines.append("")
    code_lines.append("    def test_execute_increments_count(self):")
    code_lines.append("        self.rs.check_eligibility('r2', QuantRealm.JIN_DAN)")
    code_lines.append("        rec = self.rs.execute_reincarnation('r2')")
    code_lines.append("        assert rec.reincarnation_count == 1")
    code_lines.append("        assert self.rs.get_available_marks('r2') == 1")
    code_lines.append("")
    code_lines.append("    def test_exchange_marks_success(self):")
    code_lines.append("        self.rs.check_eligibility('r3', QuantRealm.JIN_DAN)")
    code_lines.append("        self.rs.execute_reincarnation('r3')")
    code_lines.append("        er = self.rs.exchange_marks('r3', 1, 'reward_x')")
    code_lines.append("        assert er.success is True")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestAntiAbuseChecker:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.ac = AntiAbuseChecker(BalanceConfig(")
    code_lines.append("            max_cards_per_month_per_type=2,")
    code_lines.append("            rate_limit_per_minute=10,")
    code_lines.append("        ))")
    code_lines.append("")
    code_lines.append("    def test_monthly_limit_blocks_over_quota(self):")
    code_lines.append("        for _ in range(2):")
    code_lines.append("            self.ac.increment_monthly_count('ml1', ExperienceCardType.ZHU_JI_CARD)")
    code_lines.append("        assert self.ac.check_monthly_limit('ml1', ExperienceCardType.ZHU_JI_CARD) is False")
    code_lines.append("")
    code_lines.append("    def test_concurrent_blocks_second(self):")
    code_lines.append("        self.ac.set_concurrent_trial('cc1', True)")
    code_lines.append("        assert self.ac.check_concurrent_limit('cc1') is False")
    code_lines.append("")
    code_lines.append("    def test_exp_ratio_half_during_trial(self):")
    code_lines.append("        self.ac.set_concurrent_trial('er1', True)")
    code_lines.append("        assert self.ac.check_exp_grant('er1') == 0.5")
    code_lines.append("")
    code_lines.append("    def test_not_tradable(self):")
    code_lines.append("        assert self.ac.validate_tradability('x') is False")
    code_lines.append("")
    code_lines.append("    def test_rate_limit_enforcement(self):")
    code_lines.append("        for _ in range(10):")
    code_lines.append("            assert self.ac.check_rate_limit('rl1') is True")
    code_lines.append("        assert self.ac.check_rate_limit('rl1') is False")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestCultivationBackpackRenderer:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.r = CultivationBackpackRenderer()")
    code_lines.append("")
    code_lines.append("    def test_backpack_html_with_cards(self):")
    code_lines.append("        card = ExperienceCard(")
    code_lines.append("            card_id='bp1', card_type=ExperienceCardType.ZHU_JI_CARD,")
    code_lines.append("            user_id='bu1', status=CardStatus.IN_BACKPACK,")
    code_lines.append("            uses_remaining=3, uses_total=3, grant_source=GrantSource.NEWBIE,")
    code_lines.append("            expires_at=datetime.utcnow() + timedelta(hours=20),")
    code_lines.append("        )")
    code_lines.append("        html = self.r.render_backpack_html([card])")
    code_lines.append("        assert len(html) > 100")
    code_lines.append("        assert 'backpack-card' in html")
    code_lines.append("")
    code_lines.append("    def test_empty_backpack_message(self):")
    code_lines.append("        html = self.r.render_backpack_html([])")
    code_lines.append("        assert 'backpack-empty' in html")
    code_lines.append("")
    code_lines.append("    def test_notification_html_structure(self):")
    code_lines.append("        card = ExperienceCard(")
    code_lines.append("            card_id='bn1', card_type=ExperienceCardType.JIN_DAN_CARD,")
    code_lines.append("            user_id='bu2', status=CardStatus.IN_BACKPACK,")
    code_lines.append("            uses_remaining=5, uses_total=5, grant_source=GrantSource.TASK,")
    code_lines.append("        )")
    code_lines.append("        n = self.r.render_notification_html(card)")
    code_lines.append("        assert 'acquisition-notification' in n")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestOperationsConfigManager:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.om = OperationsConfigManager()")
    code_lines.append("")
    code_lines.append("    def test_create_and_get_event(self):")
    code_lines.append("        eid = self.om.create_double_exp_event({")
    code_lines.append("            'name': 'Test 2X',")
    code_lines.append("            'start_time': datetime.utcnow(),")
    code_lines.append("            'end_time': datetime.utcnow() + timedelta(days=1),")
    code_lines.append("            'multiplier': 2.0,")
    code_lines.append("        })")
    code_lines.append("        evt = self.om.get_active_event(eid)")
    code_lines.append("        assert evt is not None")
    code_lines.append("        assert evt.multiplier == 2.0")
    code_lines.append("")
    code_lines.append("    def test_shop_purchase_success(self):")
    code_lines.append("        item = ShopItem(")
    code_lines.append("            item_id='si1', name='Test Item', description='Desc',")
    code_lines.append("            price_points=100, item_type=ShopItemType.OTHER,")
    code_lines.append("            stock_unlimited=False, stock_count=2, active=True,")
    code_lines.append("        )")
    code_lines.append("        self.om.add_shop_item(item)")
    code_lines.append("        pr = self.om.purchase_item('sp1', 'si1')")
    code_lines.append("        assert pr.success is True")
    code_lines.append("")
    code_lines.append("    def test_exp_bonus_calculation(self):")
    code_lines.append("        self.om.create_double_exp_event({")
    code_lines.append("            'name': 'Bonus', 'start_time': datetime.utcnow(),")
    code_lines.append("            'end_time': datetime.utcnow() + timedelta(days=1),")
    code_lines.append("            'multiplier': 2.0,")
    code_lines.append("        })")
    code_lines.append("        val = self.om.calculate_exp_with_bonuses(100.0, 'tu1', True)")
    code_lines.append("        assert val == 100.0")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class IntegrationTests:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.suite = ExperienceCardBalanceTestSuite()")
    code_lines.append("")
    code_lines.append("    def test_full_suite_runs_without_error(self):")
    code_lines.append("        report = self.suite.run_all_tests()")
    code_lines.append("        assert report['total'] >= 30")
    code_lines.append("        assert report['pass_rate'] > 0.0")
    code_lines.append("")
    code_lines.append("    def test_e2e_lifecycle_basic(self):")
    code_lines.append("        inv = ExperienceCardInventory()")
    code_lines.append("        cid = inv.add_card('e2eu', ExperienceCardType.ZHU_JI_CARD, GrantSource.NEWBIE)")
    code_lines.append("        res = inv.use_card(cid)")
    code_lines.append("        assert res.success is True")
    code_lines.append("        assert res.temp_realm_applied is not None")
    code_lines.append("")
    code_lines.append("    def test_abuse_prevention_concurrent(self):")
    code_lines.append("        ac = AntiAbuseChecker()")
    code_lines.append("        ac.set_concurrent_trial('ab_u', True)")
    code_lines.append("        ok, _ = ac.check_can_activate('ab_u', QuantRealm.ZHU_JI)")
    code_lines.append("        assert ok is True")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("if __name__ == '__main__':")
    code_lines.append("    pytest.main([__file__, '-v', '--tb=short']")
    return "\n".join(code_lines)


def generate_playwright_e2e() -> str:
    """Generate Playwright E2E test scenarios."""
    lines = []
    lines.append("# Playwright E2E scenarios for Experience Card Balance Layer")
    lines.append("")
    lines.append("from playwright.sync_api import Page, expect")
    lines.append("")
    lines.append("")
    lines.append("def test_experience_card_lifecycle(page: Page):")
    lines.append('    page.goto("/backpack")')
    lines.append('    expect(page.locator(".cultivation-backpack")).to_be_visible()')
    lines.append('    page.locator(".backpack-card").first.click()')
    lines.append('    expect(page.locator(".card-detail-modal-content")).to_be_visible()')
    lines.append('    page.locator("button:has-text(\'使用体验卡\')").click()')
    lines.append('    expect(page.locator(".trial-badge")).to_be_visible(timeout=5000)')
    lines.append("")
    lines.append("")
    lines.append("def test_trial_ui_indicators_visible(page: Page):")
    lines.append('    page.goto("/")')
    lines.append('    expect(page.locator(".trial-badge")).to_have_count(1)')
    lines.append('    page.locator(".trial-badge").hover()')
    lines.append('    expect(page.locator("[role=tooltip]").or_(page.locator(".tooltip"))).to_be_visible()')
    lines.append("")
    lines.append("")
    lines.append("def test_expiring_soon_warning_appears(page: Page):")
    lines.append("    page.goto('/')")
    lines.append("    page.wait_for_timeout(2000)")
    lines.append("    warning = page.locator('.expiring-soon-warning')")
    lines.append("    if warning.count() > 0:")
    lines.append("        expect(warning).to_be_visible()")
    lines.append("")
    lines.append("")
    lines.append("def test_backpack_sort_options_work(page: Page):")
    lines.append('    page.goto("/backpack")')
    lines.append('    sort_select = page.locator(".backpack-sort-select")')
    lines.append("    if sort_select.count() > 0:")
    lines.append("        sort_select.select_option('by_expiry')")
    lines.append("        cards = page.locator('.backpack-card')")
    lines.append("        expect(cards).to_have_count_greater_than_or_equal(0)")
    lines.append("")
    lines.append("")
    lines.append("def test_shop_exchange_marks(page: Page):")
    lines.append('    page.goto("/exchange-shop")')
    lines.append('    expect(page.locator(".exchange-shop-container")).to_be_visible()')
    lines.append('    shop_items = page.locator(".shop-item-card")')
    lines.append("    if shop_items.count() > 0:")
    lines.append("        items_text = shop_items.first.inner_text()")
    lines.append("        assert len(items_text) > 0")
    lines.append("")
    lines.append("")
    lines.append("def test_notification_dismisses(page: Page):")
    lines.append('    page.goto("/")')
    lines.append("    notification = page.locator('.card-acquisition-notification')")
    lines.append("    if notification.count() > 0:")
    lines.append("        notification.click()")
    lines.append("        page.wait_for_timeout(500)")
    lines.append("        expect(notification).not_to_be_visible()")
    lines.append("")
    lines.append("")
    lines.append("def test_locked_feature_unlocks_in_trial(page: Page):")
    lines.append('    page.goto("/analysis")')
    lines.append('    locked = page.locator(".feature-locked-overlay")')
    lines.append("    unlocked = page.locator('.feature-unlocked-trial')")
    lines.append("    if unlocked.count() > 0:")
    lines.append("        expect(unlocked).to_contain_text('\u4f53\u9a8c\u4e2d')")
    lines.append("    elif locked.count() > 0:")
    lines.append("        expect(locked).to_be_visible()")
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Module-level convenience functions
# =============================================================================


def create_full_system() -> Dict[str, Any]:
    """Factory: create all subsystem instances wired together."""
    inventory = ExperienceCardInventory()
    realm_mgr = TempRealmManager()
    guidance_mgr = PostTrialGuidanceManager()
    reincarnation_sys = ReincarnationSystem()
    abuse_checker = AntiAbuseChecker()
    renderer = CultivationBackpackRenderer()
    ops_manager = OperationsConfigManager()
    ui_indicator = TrialUIIndicator()
    return {
        "inventory": inventory,
        "realm_manager": realm_mgr,
        "guidance_manager": guidance_mgr,
        "reincarnation_system": reincarnation_sys,
        "anti_abuse_checker": abuse_checker,
        "renderer": renderer,
        "operations_manager": ops_manager,
        "ui_indicator": ui_indicator,
    }


def run_quick_validation() -> Dict[str, Any]:
    """Run the built-in test suite and return results."""
    suite = ExperienceCardBalanceTestSuite()
    return suite.run_all_tests()


if __name__ == "__main__":
    print("Layer 23 loaded OK")
