"""
行为生物特征智能体
Behavioral Biometrics Agent

负责通过用户行为特征验证身份。
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


class BehaviorType(Enum):
    TYPING = "typing"
    MOUSE = "mouse"
    TOUCH = "touch"
    GESTURE = "gesture"
    NAVIGATION = "navigation"


class AnomalyLevel(Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    ANOMALOUS = "anomalous"
    CRITICAL = "critical"


@dataclass
class TypingPattern:
    avg_keystroke_interval: float = 0.0
    keystroke_variance: float = 0.0
    typing_speed: float = 0.0
    error_rate: float = 0.0
    pause_patterns: List[float] = field(default_factory=list)
    digraph_timings: Dict[str, float] = field(default_factory=dict)


@dataclass
class MousePattern:
    avg_speed: float = 0.0
    acceleration_profile: List[float] = field(default_factory=list)
    click_intervals: List[float] = field(default_factory=list)
    scroll_behavior: Dict = field(default_factory=dict)
    movement_smoothness: float = 0.0


@dataclass
class BehaviorProfile:
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    typing_pattern: TypingPattern = field(default_factory=TypingPattern)
    mouse_pattern: MousePattern = field(default_factory=MousePattern)
    
    navigation_patterns: Dict = field(default_factory=dict)
    session_patterns: Dict = field(default_factory=dict)
    
    sample_count: int = 0
    confidence_score: float = 0.0
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class BehaviorVerificationResult:
    verification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    anomaly_level: str = AnomalyLevel.NORMAL.value
    anomaly_score: float = 0.0
    
    typing_score: float = 1.0
    mouse_score: float = 1.0
    navigation_score: float = 1.0
    
    anomalies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BehavioralBiometricsAgent:
    """
    行为生物特征智能体
    
    功能：
    1. 击键动力学：分析打字速度、按键间隔、错误率
    2. 鼠标行为：分析移动轨迹、点击模式、滚动行为
    3. 触屏手势：分析滑动速度、压力、轨迹
    4. 导航模式：分析页面访问顺序、停留时间
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "BehavioralBiometricsAgent"
        self.description = "通过用户行为特征验证身份"
        self.config = config or {}
        
        self.profiles: Dict[str, BehaviorProfile] = {}
        self.user_profiles: Dict[str, str] = {}
        self.verification_history: List[BehaviorVerificationResult] = []
        
        self.anomaly_thresholds = {
            "typing": 0.3,
            "mouse": 0.3,
            "navigation": 0.4,
        }
        
        self.min_samples_for_profile = 5
        
        self.stats = {
            "total_profiles": 0,
            "total_verifications": 0,
            "anomalies_detected": 0,
            "anomalies_by_level": defaultdict(int),
            "anomalies_by_type": defaultdict(int),
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def record_behavior(
        self,
        user_id: str,
        behavior_type: str,
        behavior_data: Dict,
    ) -> Dict:
        profile_id = self.user_profiles.get(user_id)
        
        if not profile_id:
            profile = BehaviorProfile(user_id=user_id)
            self.profiles[profile.profile_id] = profile
            self.user_profiles[user_id] = profile.profile_id
            self.stats["total_profiles"] += 1
        else:
            profile = self.profiles.get(profile_id)
        
        if not profile:
            return {"success": False, "reason": "无法获取行为档案"}
        
        if behavior_type == BehaviorType.TYPING.value:
            self._update_typing_pattern(profile, behavior_data)
        elif behavior_type == BehaviorType.MOUSE.value:
            self._update_mouse_pattern(profile, behavior_data)
        elif behavior_type == BehaviorType.NAVIGATION.value:
            self._update_navigation_pattern(profile, behavior_data)
        
        profile.sample_count += 1
        profile.updated_at = datetime.utcnow().isoformat()
        
        if profile.sample_count >= self.min_samples_for_profile:
            profile.confidence_score = min(1.0, profile.sample_count / 20)
        
        return {
            "success": True,
            "sample_count": profile.sample_count,
            "confidence_score": profile.confidence_score,
        }
    
    def _update_typing_pattern(self, profile: BehaviorProfile, data: Dict):
        keystroke_intervals = data.get("keystroke_intervals", [])
        if keystroke_intervals:
            profile.typing_pattern.avg_keystroke_interval = (
                sum(keystroke_intervals) / len(keystroke_intervals)
            )
            variance = sum(
                (x - profile.typing_pattern.avg_keystroke_interval) ** 2
                for x in keystroke_intervals
            ) / len(keystroke_intervals)
            profile.typing_pattern.keystroke_variance = variance
        
        profile.typing_pattern.typing_speed = data.get("typing_speed", profile.typing_pattern.typing_speed)
        profile.typing_pattern.error_rate = data.get("error_rate", profile.typing_pattern.error_rate)
        
        digraphs = data.get("digraph_timings", {})
        profile.typing_pattern.digraph_timings.update(digraphs)
    
    def _update_mouse_pattern(self, profile: BehaviorProfile, data: Dict):
        profile.mouse_pattern.avg_speed = data.get("avg_speed", profile.mouse_pattern.avg_speed)
        profile.mouse_pattern.movement_smoothness = data.get("movement_smoothness", profile.mouse_pattern.movement_smoothness)
        
        click_intervals = data.get("click_intervals", [])
        if click_intervals:
            profile.mouse_pattern.click_intervals.extend(click_intervals[-10:])
    
    def _update_navigation_pattern(self, profile: BehaviorProfile, data: Dict):
        page = data.get("page", "")
        duration = data.get("duration", 0)
        
        if page not in profile.navigation_patterns:
            profile.navigation_patterns[page] = {
                "visit_count": 0,
                "avg_duration": 0,
            }
        
        nav = profile.navigation_patterns[page]
        nav["visit_count"] += 1
        nav["avg_duration"] = (
            (nav["avg_duration"] * (nav["visit_count"] - 1) + duration) /
            nav["visit_count"]
        )
    
    async def verify_behavior(
        self,
        user_id: str,
        current_behavior: Dict,
    ) -> BehaviorVerificationResult:
        self.stats["total_verifications"] += 1
        
        profile_id = self.user_profiles.get(user_id)
        
        if not profile_id:
            return BehaviorVerificationResult(
                user_id=user_id,
                anomaly_level=AnomalyLevel.SUSPICIOUS.value,
                anomaly_score=0.5,
                anomalies=["用户无行为档案"],
            )
        
        profile = self.profiles.get(profile_id)
        if not profile:
            return BehaviorVerificationResult(
                user_id=user_id,
                anomaly_level=AnomalyLevel.SUSPICIOUS.value,
                anomaly_score=0.5,
                anomalies=["行为档案不存在"],
            )
        
        anomalies = []
        typing_score = 1.0
        mouse_score = 1.0
        navigation_score = 1.0
        
        if "typing" in current_behavior:
            typing_score, typing_anomalies = self._verify_typing(
                profile, current_behavior["typing"]
            )
            anomalies.extend(typing_anomalies)
        
        if "mouse" in current_behavior:
            mouse_score, mouse_anomalies = self._verify_mouse(
                profile, current_behavior["mouse"]
            )
            anomalies.extend(mouse_anomalies)
        
        if "navigation" in current_behavior:
            navigation_score, nav_anomalies = self._verify_navigation(
                profile, current_behavior["navigation"]
            )
            anomalies.extend(nav_anomalies)
        
        anomaly_score = 1 - (typing_score * 0.4 + mouse_score * 0.3 + navigation_score * 0.3)
        
        if anomaly_score >= 0.7:
            anomaly_level = AnomalyLevel.CRITICAL.value
        elif anomaly_score >= 0.5:
            anomaly_level = AnomalyLevel.ANOMALOUS.value
        elif anomaly_score >= 0.3:
            anomaly_level = AnomalyLevel.SUSPICIOUS.value
        else:
            anomaly_level = AnomalyLevel.NORMAL.value
        
        if anomaly_level != AnomalyLevel.NORMAL.value:
            self.stats["anomalies_detected"] += 1
            self.stats["anomalies_by_level"][anomaly_level] += 1
            for anomaly in anomalies:
                self.stats["anomalies_by_type"][anomaly] += 1
        
        result = BehaviorVerificationResult(
            user_id=user_id,
            anomaly_level=anomaly_level,
            anomaly_score=anomaly_score,
            typing_score=typing_score,
            mouse_score=mouse_score,
            navigation_score=navigation_score,
            anomalies=anomalies,
        )
        
        self.verification_history.append(result)
        
        return result
    
    def _verify_typing(
        self,
        profile: BehaviorProfile,
        current: Dict,
    ) -> tuple:
        score = 1.0
        anomalies = []
        
        current_speed = current.get("typing_speed", 0)
        expected_speed = profile.typing_pattern.typing_speed
        
        if expected_speed > 0:
            speed_diff = abs(current_speed - expected_speed) / expected_speed
            if speed_diff > self.anomaly_thresholds["typing"]:
                score -= 0.3
                anomalies.append(f"打字速度异常: 当前{current_speed:.1f}, 预期{expected_speed:.1f}")
        
        current_interval = current.get("avg_keystroke_interval", 0)
        expected_interval = profile.typing_pattern.avg_keystroke_interval
        
        if expected_interval > 0:
            interval_diff = abs(current_interval - expected_interval) / expected_interval
            if interval_diff > self.anomaly_thresholds["typing"]:
                score -= 0.3
                anomalies.append("按键间隔模式异常")
        
        current_error = current.get("error_rate", 0)
        expected_error = profile.typing_pattern.error_rate
        
        if abs(current_error - expected_error) > 0.1:
            score -= 0.2
            anomalies.append("错误率异常")
        
        return max(0, score), anomalies
    
    def _verify_mouse(
        self,
        profile: BehaviorProfile,
        current: Dict,
    ) -> tuple:
        score = 1.0
        anomalies = []
        
        current_speed = current.get("avg_speed", 0)
        expected_speed = profile.mouse_pattern.avg_speed
        
        if expected_speed > 0:
            speed_diff = abs(current_speed - expected_speed) / expected_speed
            if speed_diff > self.anomaly_thresholds["mouse"]:
                score -= 0.3
                anomalies.append("鼠标移动速度异常")
        
        current_smoothness = current.get("movement_smoothness", 0)
        expected_smoothness = profile.mouse_pattern.movement_smoothness
        
        if expected_smoothness > 0:
            smoothness_diff = abs(current_smoothness - expected_smoothness)
            if smoothness_diff > 0.3:
                score -= 0.3
                anomalies.append("鼠标移动平滑度异常")
        
        return max(0, score), anomalies
    
    def _verify_navigation(
        self,
        profile: BehaviorProfile,
        current: Dict,
    ) -> tuple:
        score = 1.0
        anomalies = []
        
        current_page = current.get("page", "")
        current_duration = current.get("duration", 0)
        
        if current_page in profile.navigation_patterns:
            expected_duration = profile.navigation_patterns[current_page].get("avg_duration", 0)
            
            if expected_duration > 0:
                duration_diff = abs(current_duration - expected_duration) / expected_duration
                if duration_diff > self.anomaly_thresholds["navigation"]:
                    score -= 0.2
                    anomalies.append("页面停留时间异常")
        else:
            score -= 0.1
        
        return max(0, score), anomalies
    
    async def get_profile(self, user_id: str) -> Optional[Dict]:
        profile_id = self.user_profiles.get(user_id)
        if not profile_id:
            return None
        
        profile = self.profiles.get(profile_id)
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "sample_count": profile.sample_count,
            "confidence_score": profile.confidence_score,
            "typing_pattern": {
                "avg_keystroke_interval": profile.typing_pattern.avg_keystroke_interval,
                "typing_speed": profile.typing_pattern.typing_speed,
            },
            "mouse_pattern": {
                "avg_speed": profile.mouse_pattern.avg_speed,
                "movement_smoothness": profile.mouse_pattern.movement_smoothness,
            },
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
    
    async def reset_profile(self, user_id: str) -> bool:
        profile_id = self.user_profiles.get(user_id)
        if not profile_id:
            return False
        
        if profile_id in self.profiles:
            del self.profiles[profile_id]
        
        del self.user_profiles[user_id]
        return True
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_profiles": self.stats["total_profiles"],
            "total_verifications": self.stats["total_verifications"],
            "anomalies_detected": self.stats["anomalies_detected"],
            "anomalies_by_level": dict(self.stats["anomalies_by_level"]),
            "anomalies_by_type": dict(self.stats["anomalies_by_type"]),
        }
