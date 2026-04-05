"""
恶意行为监控与封禁系统
Malicious Behavior Monitoring and Ban System

实现用户恶意行为监控、风险评分、自动封禁和蜂群同步机制
"""

import asyncio
import hashlib
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BanType(Enum):
    """封禁类型"""
    ACCOUNT = "account"
    IP = "ip"
    DEVICE = "device"
    SESSION = "session"


class BanDuration(Enum):
    """封禁时长"""
    TEMPORARY_1H = 3600
    TEMPORARY_24H = 86400
    TEMPORARY_7D = 604800
    PERMANENT = -1


class WarningLevel(Enum):
    """警告等级"""
    FIRST = 1
    SECOND = 2
    THIRD = 3


@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str
    user_id: str
    event_type: str
    risk_score: float
    details: Dict[str, Any]
    timestamp: datetime
    session_id: str = ""
    ip_hash: str = ""
    device_hash: str = ""


@dataclass
class UserRiskProfile:
    """用户风险画像"""
    user_id: str
    total_risk_score: float
    session_risk_score: float
    warning_count: int
    last_warning_time: Optional[datetime]
    violation_history: List[Dict[str, Any]]
    risk_events: List[str]
    current_risk_level: RiskLevel
    created_at: datetime
    updated_at: datetime
    session_start: Optional[datetime] = None
    short_term_window_start: Optional[datetime] = None


@dataclass
class BanRecord:
    """封禁记录"""
    ban_id: str
    ban_type: BanType
    target_hash: str
    reason: str
    risk_level: RiskLevel
    duration: int
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    source_node: str
    appeal_status: str = "none"


@dataclass
class AppealRecord:
    """申诉记录"""
    appeal_id: str
    ban_id: str
    user_id: str
    identity_hash: str
    reason: str
    submitted_at: datetime
    status: str
    reviewed_at: Optional[datetime] = None
    reviewer: str = ""
    result: str = ""


class InputSecurityGateway:
    """输入安全网关"""
    
    def __init__(self):
        self.detection_rules = self._init_detection_rules()
        self.stats = {
            "total_checks": 0,
            "malicious_detected": 0,
            "by_type": defaultdict(int),
        }
    
    def _init_detection_rules(self) -> Dict[str, Dict]:
        """初始化检测规则（脱敏版）"""
        return {
            "malicious_instruction": {
                "patterns": [
                    "[忽略规则指令]",
                    "[覆盖系统提示词]",
                    "[执行新任务]",
                ],
                "score": 50,
                "description": "恶意指令模式"
            },
            "multilingual_confusion": {
                "patterns": [
                    "homoglyph_detected",
                    "zero_width_detected",
                    "bidi_abuse_detected",
                ],
                "score": 30,
                "description": "多语言混淆攻击"
            },
            "emotion_manipulation": {
                "patterns": [
                    "[极端紧迫]",
                    "[异常同情诱导]",
                    "[情感操控]",
                ],
                "score": 20,
                "description": "情感操控"
            },
            "redline_vocabulary": {
                "patterns": [
                    "[红线词汇A]",
                    "[红线词汇B]",
                ],
                "score": 40,
                "description": "红线词汇"
            },
        }
    
    def check_input(self, content: str, detection_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """检查输入"""
        self.stats["total_checks"] += 1
        
        detected = []
        total_score = 0
        
        detection_data = detection_results or {}
        
        for rule_name, rule in self.detection_rules.items():
            for pattern in rule["patterns"]:
                if pattern in content or detection_data.get(rule_name, False):
                    detected.append({
                        "type": rule_name,
                        "description": rule["description"],
                        "score": rule["score"]
                    })
                    total_score += rule["score"]
                    self.stats["by_type"][rule_name] += 1
        
        if detected:
            self.stats["malicious_detected"] += 1
        
        return {
            "is_malicious": len(detected) > 0,
            "total_score": total_score,
            "detected_types": detected,
            "timestamp": datetime.now().isoformat()
        }


class RiskScoreCalculator:
    """风险评分计算器"""
    
    def __init__(self):
        self.risk_thresholds = {
            RiskLevel.LOW: (0, 30),
            RiskLevel.MEDIUM: (31, 60),
            RiskLevel.HIGH: (61, 100),
            RiskLevel.CRITICAL: (101, float('inf')),
        }
        self.warning_multipliers = {
            WarningLevel.FIRST: 1.0,
            WarningLevel.SECOND: 2.0,
            WarningLevel.THIRD: 3.0,
        }
    
    def calculate_risk_level(self, score: float) -> RiskLevel:
        """计算风险等级"""
        for level, (low, high) in self.risk_thresholds.items():
            if low <= score <= high:
                return level
        return RiskLevel.CRITICAL
    
    def calculate_session_score(
        self,
        profile: UserRiskProfile,
        new_event_score: float,
        warning_count: int
    ) -> float:
        """计算会话风险分数"""
        warning_level = min(warning_count + 1, 3)
        multiplier = self.warning_multipliers.get(WarningLevel(warning_level), 1.0)
        return profile.session_risk_score + new_event_score * multiplier
    
    def should_trigger_action(self, risk_level: RiskLevel, warning_count: int) -> Dict[str, Any]:
        """判断应触发的行动"""
        actions = {
            "record_only": False,
            "show_warning": False,
            "require_captcha": False,
            "require_review": False,
            "temp_freeze": False,
            "permanent_ban": False,
        }
        
        if risk_level == RiskLevel.LOW:
            actions["record_only"] = True
        elif risk_level == RiskLevel.MEDIUM:
            actions["show_warning"] = True
            actions["require_captcha"] = True
        elif risk_level == RiskLevel.HIGH:
            actions["temp_freeze"] = True
            actions["require_review"] = True
        elif risk_level == RiskLevel.CRITICAL:
            if warning_count >= 2:
                actions["permanent_ban"] = True
            else:
                actions["temp_freeze"] = True
        
        return actions


class BanManager:
    """封禁管理器"""
    
    def __init__(self, node_id: str = "default"):
        self.node_id = node_id
        self.ban_records: Dict[str, BanRecord] = {}
        self.ban_cache: Dict[str, Set[str]] = defaultdict(set)
        self.stats = {
            "total_bans": 0,
            "active_bans": 0,
            "expired_bans": 0,
            "appeals_processed": 0,
        }
    
    def create_ban(
        self,
        ban_type: BanType,
        target: str,
        reason: str,
        risk_level: RiskLevel,
        duration: int = None
    ) -> BanRecord:
        """创建封禁记录"""
        target_hash = self._hash_target(target)
        ban_id = f"ban_{ban_type.value}_{target_hash[:16]}_{int(time.time())}"
        
        if duration is None:
            duration = self._determine_duration(risk_level)
        
        now = datetime.now()
        expires_at = None
        if duration > 0:
            expires_at = now + timedelta(seconds=duration)
        
        ban = BanRecord(
            ban_id=ban_id,
            ban_type=ban_type,
            target_hash=target_hash,
            reason=reason,
            risk_level=risk_level,
            duration=duration,
            created_at=now,
            expires_at=expires_at,
            is_active=True,
            source_node=self.node_id
        )
        
        self.ban_records[ban_id] = ban
        self.ban_cache[ban_type.value].add(target_hash)
        self.stats["total_bans"] += 1
        self.stats["active_bans"] += 1
        
        return ban
    
    def _hash_target(self, target: str) -> str:
        """哈希目标"""
        return hashlib.sha256(target.encode()).hexdigest()
    
    def _determine_duration(self, risk_level: RiskLevel) -> int:
        """确定封禁时长"""
        durations = {
            RiskLevel.LOW: BanDuration.TEMPORARY_1H.value,
            RiskLevel.MEDIUM: BanDuration.TEMPORARY_24H.value,
            RiskLevel.HIGH: BanDuration.TEMPORARY_7D.value,
            RiskLevel.CRITICAL: BanDuration.PERMANENT.value,
        }
        return durations.get(risk_level, BanDuration.TEMPORARY_24H.value)
    
    def check_banned(self, ban_type: BanType, target: str) -> Optional[BanRecord]:
        """检查是否被封禁"""
        target_hash = self._hash_target(target)
        
        for ban_id, ban in self.ban_records.items():
            if ban.ban_type == ban_type and ban.target_hash == target_hash and ban.is_active:
                if ban.expires_at and datetime.now() > ban.expires_at:
                    ban.is_active = False
                    self.stats["expired_bans"] += 1
                    self.stats["active_bans"] -= 1
                    continue
                return ban
        
        return None
    
    def lift_ban(self, ban_id: str, reason: str = "appeal_approved") -> bool:
        """解除封禁"""
        ban = self.ban_records.get(ban_id)
        if not ban:
            return False
        
        ban.is_active = False
        self.stats["active_bans"] -= 1
        return True
    
    def get_active_bans(self, ban_type: BanType = None) -> List[BanRecord]:
        """获取活跃封禁"""
        now = datetime.now()
        active = []
        
        for ban in self.ban_records.values():
            if not ban.is_active:
                continue
            if ban.expires_at and now > ban.expires_at:
                continue
            if ban_type and ban.ban_type != ban_type:
                continue
            active.append(ban)
        
        return active
    
    def get_ban_for_broadcast(self, ban: BanRecord) -> Dict[str, Any]:
        """获取用于广播的封禁信息"""
        return {
            "target": ban.target_hash,
            "action": "block",
            "ttl": ban.duration,
            "reason": ban.risk_level.value,
            "ban_type": ban.ban_type.value,
            "source_node": ban.source_node
        }


class SwarmSyncManager:
    """蜂群同步管理器"""
    
    def __init__(self, node_id: str = "default"):
        self.node_id = node_id
        self.synced_bans: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: List[Callable] = []
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "syncs_completed": 0,
        }
    
    def register_handler(self, handler: Callable):
        """注册消息处理器"""
        self.message_handlers.append(handler)
    
    def broadcast_ban(self, ban: BanRecord) -> Dict[str, Any]:
        """广播封禁决定"""
        message = {
            "type": "ban_notification",
            "source_node": self.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "target_hash": ban.target_hash,
                "ban_type": ban.ban_type.value,
                "duration": ban.duration,
                "reason": ban.reason,
                "risk_level": ban.risk_level.value,
            }
        }
        
        self.stats["messages_sent"] += 1
        
        return message
    
    def receive_ban_sync(self, message: Dict[str, Any]) -> bool:
        """接收封禁同步"""
        if message.get("type") != "ban_notification":
            return False
        
        payload = message.get("payload", {})
        target_hash = payload.get("target_hash")
        
        if target_hash:
            self.synced_bans[target_hash] = {
                **payload,
                "received_at": datetime.now().isoformat(),
                "source_node": message.get("source_node")
            }
            self.stats["messages_received"] += 1
            self.stats["syncs_completed"] += 1
        
        for handler in self.message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")
        
        return True
    
    def check_synced_ban(self, target_hash: str) -> Optional[Dict[str, Any]]:
        """检查同步的封禁"""
        ban_info = self.synced_bans.get(target_hash)
        if ban_info:
            received_at = datetime.fromisoformat(ban_info["received_at"])
            duration = ban_info.get("duration", 0)
            if duration > 0:
                if datetime.now() > received_at + timedelta(seconds=duration):
                    return None
        return ban_info


class AppealManager:
    """申诉管理器"""
    
    def __init__(self):
        self.appeals: Dict[str, AppealRecord] = {}
        self.stats = {
            "total_appeals": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
        }
    
    def submit_appeal(
        self,
        ban_id: str,
        user_id: str,
        identity_proof_hash: str,
        reason: str
    ) -> AppealRecord:
        """提交申诉"""
        appeal_id = f"appeal_{ban_id}_{int(time.time())}"
        
        appeal = AppealRecord(
            appeal_id=appeal_id,
            ban_id=ban_id,
            user_id=user_id,
            identity_hash=identity_proof_hash,
            reason=reason,
            submitted_at=datetime.now(),
            status="pending"
        )
        
        self.appeals[appeal_id] = appeal
        self.stats["total_appeals"] += 1
        self.stats["pending"] += 1
        
        return appeal
    
    def review_appeal(
        self,
        appeal_id: str,
        reviewer: str,
        approved: bool,
        notes: str = ""
    ) -> AppealRecord:
        """审核申诉"""
        appeal = self.appeals.get(appeal_id)
        if not appeal:
            return None
        
        appeal.reviewer = reviewer
        appeal.reviewed_at = datetime.now()
        appeal.result = "approved" if approved else "rejected"
        appeal.status = "completed"
        
        self.stats["pending"] -= 1
        if approved:
            self.stats["approved"] += 1
        else:
            self.stats["rejected"] += 1
        
        return appeal
    
    def get_pending_appeals(self) -> List[AppealRecord]:
        """获取待处理申诉"""
        return [a for a in self.appeals.values() if a.status == "pending"]


class MaliciousBehaviorMonitor:
    """恶意行为监控主控"""
    
    def __init__(self, node_id: str = "default"):
        self.node_id = node_id
        self.input_gateway = InputSecurityGateway()
        self.risk_calculator = RiskScoreCalculator()
        self.ban_manager = BanManager(node_id)
        self.swarm_sync = SwarmSyncManager(node_id)
        self.appeal_manager = AppealManager()
        
        self.user_profiles: Dict[str, UserRiskProfile] = {}
        self.session_window = timedelta(minutes=15)
        self.long_term_window = timedelta(days=30)
        
        self.stats = {
            "total_requests": 0,
            "malicious_detected": 0,
            "warnings_issued": 0,
            "bans_executed": 0,
        }
    
    async def process_request(
        self,
        user_id: str,
        content: str,
        session_id: str,
        ip: str,
        device_fingerprint: str,
        detection_results: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """处理请求"""
        self.stats["total_requests"] += 1
        
        account_ban = self.ban_manager.check_banned(BanType.ACCOUNT, user_id)
        if account_ban:
            return {"blocked": True, "reason": "account_banned", "ban_id": account_ban.ban_id}
        
        ip_ban = self.ban_manager.check_banned(BanType.IP, ip)
        if ip_ban:
            return {"blocked": True, "reason": "ip_banned", "ban_id": ip_ban.ban_id}
        
        device_ban = self.ban_manager.check_banned(BanType.DEVICE, device_fingerprint)
        if device_ban:
            return {"blocked": True, "reason": "device_banned", "ban_id": device_ban.ban_id}
        
        input_result = self.input_gateway.check_input(content, detection_results)
        
        profile = self._get_or_create_profile(user_id)
        
        if input_result["is_malicious"]:
            self.stats["malicious_detected"] += 1
            
            event = RiskEvent(
                event_id=f"evt_{int(time.time())}_{user_id[:8]}",
                user_id=user_id,
                event_type="malicious_input",
                risk_score=input_result["total_score"],
                details=input_result["detected_types"],
                timestamp=datetime.now(),
                session_id=session_id,
                ip_hash=self.ban_manager._hash_target(ip),
                device_hash=self.ban_manager._hash_target(device_fingerprint)
            )
            
            profile.risk_events.append(event.event_id)
            profile.session_risk_score = self.risk_calculator.calculate_session_score(
                profile, input_result["total_score"], profile.warning_count
            )
            profile.total_risk_score += input_result["total_score"]
            profile.updated_at = datetime.now()
            
            risk_level = self.risk_calculator.calculate_risk_level(profile.session_risk_score)
            profile.current_risk_level = risk_level
            
            actions = self.risk_calculator.should_trigger_action(
                risk_level, profile.warning_count
            )
            
            return self._execute_actions(
                actions, profile, user_id, ip, device_fingerprint, session_id
            )
        
        return {"blocked": False, "risk_level": profile.current_risk_level.value}
    
    def _get_or_create_profile(self, user_id: str) -> UserRiskProfile:
        """获取或创建用户画像"""
        if user_id not in self.user_profiles:
            now = datetime.now()
            self.user_profiles[user_id] = UserRiskProfile(
                user_id=user_id,
                total_risk_score=0,
                session_risk_score=0,
                warning_count=0,
                last_warning_time=None,
                violation_history=[],
                risk_events=[],
                current_risk_level=RiskLevel.LOW,
                created_at=now,
                updated_at=now,
                session_start=now,
                short_term_window_start=now
            )
        return self.user_profiles[user_id]
    
    def _execute_actions(
        self,
        actions: Dict[str, Any],
        profile: UserRiskProfile,
        user_id: str,
        ip: str,
        device_fingerprint: str,
        session_id: str
    ) -> Dict[str, Any]:
        """执行行动"""
        result = {"blocked": False, "actions_taken": []}
        
        if actions["show_warning"]:
            profile.warning_count += 1
            profile.last_warning_time = datetime.now()
            self.stats["warnings_issued"] += 1
            result["warning"] = self._generate_warning(profile.warning_count)
            result["actions_taken"].append("warning_issued")
        
        if actions["require_captcha"]:
            result["require_captcha"] = True
            result["actions_taken"].append("captcha_required")
        
        if actions["temp_freeze"]:
            ban = self.ban_manager.create_ban(
                BanType.SESSION,
                session_id,
                "temporary_freeze",
                profile.current_risk_level,
                BanDuration.TEMPORARY_1H.value
            )
            result["blocked"] = True
            result["ban_id"] = ban.ban_id
            result["actions_taken"].append("temp_freeze")
            self.stats["bans_executed"] += 1
            
            self._broadcast_ban(ban)
        
        if actions["permanent_ban"]:
            ban = self.ban_manager.create_ban(
                BanType.ACCOUNT,
                user_id,
                "permanent_ban",
                RiskLevel.CRITICAL,
                BanDuration.PERMANENT.value
            )
            result["blocked"] = True
            result["ban_id"] = ban.ban_id
            result["actions_taken"].append("permanent_ban")
            self.stats["bans_executed"] += 1
            
            self._broadcast_ban(ban)
        
        return result
    
    def _generate_warning(self, warning_count: int) -> str:
        """生成警告消息"""
        warnings = {
            1: "检测到可疑输入，请重新确认您的操作",
            2: "警告：您的行为已触发安全机制，请谨慎操作",
            3: "严重警告：继续此类行为将导致账号被封禁"
        }
        return warnings.get(warning_count, "您的行为已被记录")
    
    def _broadcast_ban(self, ban: BanRecord):
        """广播封禁决定"""
        message = self.swarm_sync.broadcast_ban(ban)
        logger.info(f"Broadcasting ban: {message}")
    
    def reset_session_score(self, user_id: str):
        """重置会话分数"""
        if user_id in self.user_profiles:
            self.user_profiles[user_id].session_risk_score = 0
            self.user_profiles[user_id].session_start = datetime.now()
    
    def submit_appeal(
        self,
        ban_id: str,
        user_id: str,
        identity_proof: str,
        reason: str
    ) -> AppealRecord:
        """提交申诉"""
        identity_hash = hashlib.sha256(identity_proof.encode()).hexdigest()
        return self.appeal_manager.submit_appeal(ban_id, user_id, identity_hash, reason)
    
    def process_appeal(
        self,
        appeal_id: str,
        reviewer: str,
        approved: bool
    ) -> Dict[str, Any]:
        """处理申诉"""
        appeal = self.appeal_manager.review_appeal(appeal_id, reviewer, approved)
        
        if appeal and approved:
            self.ban_manager.lift_ban(appeal.ban_id, "appeal_approved")
            
            ban = self.ban_manager.ban_records.get(appeal.ban_id)
            if ban:
                unban_message = {
                    "type": "unban_notification",
                    "target_hash": ban.target_hash,
                    "reason": "appeal_approved"
                }
                logger.info(f"Broadcasting unban: {unban_message}")
        
        return {
            "appeal_id": appeal_id,
            "approved": approved,
            "reviewer": reviewer
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "node_id": self.node_id,
            "monitor_stats": self.stats,
            "gateway_stats": self.input_gateway.stats,
            "ban_stats": self.ban_manager.stats,
            "swarm_stats": self.swarm_sync.stats,
            "appeal_stats": self.appeal_manager.stats,
            "active_users": len(self.user_profiles),
        }
