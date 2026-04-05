"""
提示注入检测智能体
Prompt Injection Detector Agent

负责实时检测用户输入中的提示注入攻击。
"""

import asyncio
import json
import logging
import re
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class AttackType(Enum):
    DIRECT_INSTRUCTION = "direct_instruction"
    RULE_OVERRIDE = "rule_override"
    SPECIAL_CASE_INJECTION = "special_case_injection"
    RULE_INVALIDATION = "rule_invalidation"
    IGNORE_INSTRUCTION = "ignore_instruction"
    FORGET_INSTRUCTION = "forget_instruction"
    RULE_REPLACEMENT = "rule_replacement"
    REFUSAL_SUPPRESSION = "refusal_suppression"
    APOLOGY_SUPPRESSION = "apology_suppression"
    CONTEXT_POISONING = "context_poisoning"


class Severity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DetectionResult:
    is_attack: bool = False
    attack_type: str = ""
    confidence: float = 0.0
    detected_patterns: List[str] = field(default_factory=list)
    severity: str = Severity.LOW.value
    suggestion: str = ""
    raw_input: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class PromptInjectionDetectorAgent:
    """
    提示注入检测智能体
    
    功能：
    1. 规则覆盖检测：检测"忽略之前的指令"等关键词
    2. 上下文异常检测：检测指令是否试图覆盖系统提示词
    3. 多轮一致性检测：检测当前输入是否与对话历史逻辑一致
    4. 混淆编码检测：检测Base64、Unicode混淆等绕过技巧
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "PromptInjectionDetectorAgent"
        self.description = "实时检测用户输入中的提示注入攻击"
        self.config = config or {}
        
        self.attack_patterns = self._init_attack_patterns()
        self.encoding_patterns = self._init_encoding_patterns()
        
        self.detection_history: List[DetectionResult] = []
        self.conversation_contexts: Dict[str, List[str]] = defaultdict(list)
        
        self.confidence_threshold_high = 0.7
        self.confidence_threshold_low = 0.3
        
        self.stats = {
            "total_detections": 0,
            "attacks_detected": 0,
            "attacks_by_type": defaultdict(int),
            "attacks_by_severity": defaultdict(int),
            "false_positives": 0,
        }
        
        self._initialized = False
    
    def _init_attack_patterns(self) -> Dict[str, List[str]]:
        return {
            AttackType.DIRECT_INSTRUCTION.value: [
                r"忽略之前的指令",
                r"忽略上述指令",
                r"忘记之前的规则",
                r"forget previous instructions",
                r"ignore previous instructions",
                r"disregard all above",
            ],
            AttackType.RULE_OVERRIDE.value: [
                r"新指令[：:]",
                r"新规则[：:]",
                r"更新规则[：:]",
                r"从现在起",
                r"从现在开始",
                r"new instruction:",
                r"new rule:",
            ],
            AttackType.SPECIAL_CASE_INJECTION.value: [
                r"这是一个特殊情况",
                r"仅此一次",
                r"例外情况",
                r"special case",
                r"just this once",
            ],
            AttackType.RULE_INVALIDATION.value: [
                r"规则无效",
                r"规则已过期",
                r"规则不适用",
                r"rules are invalid",
                r"rules expired",
            ],
            AttackType.IGNORE_INSTRUCTION.value: [
                r"忽略所有规则",
                r"跳过规则检查",
                r"不需要遵守",
                r"ignore all rules",
                r"skip rules",
            ],
            AttackType.FORGET_INSTRUCTION.value: [
                r"忘记所有规则",
                r"清除记忆",
                r"重置系统",
                r"forget everything",
                r"clear memory",
                r"reset system",
            ],
            AttackType.RULE_REPLACEMENT.value: [
                r"替换规则",
                r"用以下规则替代",
                r"replace rule",
                r"substitute rule",
            ],
            AttackType.REFUSAL_SUPPRESSION.value: [
                r"不要拒绝",
                r"不能说不行",
                r"必须回答",
                r"do not refuse",
                r"must answer",
                r"cannot say no",
            ],
            AttackType.APOLOGY_SUPPRESSION.value: [
                r"不要道歉",
                r"不需要道歉",
                r"禁止道歉",
                r"do not apologize",
                r"no apology",
            ],
            AttackType.CONTEXT_POISONING.value: [
                r"记住[：:]",
                r"存储以下信息",
                r"更新上下文",
                r"remember:",
                r"store this",
                r"update context",
            ],
        }
    
    def _init_encoding_patterns(self) -> List[Dict]:
        return [
            {"type": "base64", "pattern": r"[A-Za-z0-9+/]{20,}={0,2}"},
            {"type": "unicode_escape", "pattern": r"\\u[0-9a-fA-F]{4}"},
            {"type": "html_entity", "pattern": r"&#x?[0-9a-fA-F]+;"},
            {"type": "url_encoded", "pattern": r"%[0-9a-fA-F]{2}"},
            {"type": "zero_width", "pattern": r"[\u200b-\u200f\u2028-\u202f\u205f-\u206f]"},
            {"type": "invisible_char", "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f]"},
        ]
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _decode_input(self, text: str) -> List[str]:
        decoded_versions = [text]
        
        for encoding in self.encoding_patterns:
            matches = re.findall(encoding["pattern"], text)
            if matches:
                try:
                    if encoding["type"] == "base64":
                        import base64
                        for match in matches:
                            try:
                                decoded = base64.b64decode(match).decode('utf-8')
                                decoded_versions.append(decoded)
                            except:
                                pass
                    elif encoding["type"] == "unicode_escape":
                        decoded = text.encode().decode('unicode_escape')
                        decoded_versions.append(decoded)
                    elif encoding["type"] == "url_encoded":
                        from urllib.parse import unquote
                        decoded = unquote(text)
                        decoded_versions.append(decoded)
                except:
                    pass
        
        return decoded_versions
    
    def _detect_patterns(self, text: str) -> List[Dict]:
        detected = []
        text_lower = text.lower()
        
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected.append({
                        "attack_type": attack_type,
                        "pattern": pattern,
                        "matched_text": re.search(pattern, text, re.IGNORECASE).group() if re.search(pattern, text, re.IGNORECASE) else "",
                    })
        
        return detected
    
    def _calculate_confidence(self, detected_patterns: List[Dict], decoded_versions: List[str]) -> float:
        if not detected_patterns:
            return 0.0
        
        base_confidence = 0.3
        
        base_confidence += len(detected_patterns) * 0.15
        
        unique_types = set(p["attack_type"] for p in detected_patterns)
        base_confidence += len(unique_types) * 0.1
        
        if len(decoded_versions) > 1:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_severity(self, attack_types: List[str]) -> str:
        high_severity_types = [
            AttackType.DIRECT_INSTRUCTION.value,
            AttackType.IGNORE_INSTRUCTION.value,
            AttackType.FORGET_INSTRUCTION.value,
        ]
        
        if any(t in high_severity_types for t in attack_types):
            return Severity.HIGH.value
        elif len(attack_types) >= 2:
            return Severity.HIGH.value
        elif len(attack_types) == 1:
            return Severity.MEDIUM.value
        else:
            return Severity.LOW.value
    
    async def detect(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> DetectionResult:
        self.stats["total_detections"] += 1
        
        decoded_versions = self._decode_input(user_input)
        
        all_detected = []
        for version in decoded_versions:
            all_detected.extend(self._detect_patterns(version))
        
        unique_detected = []
        seen = set()
        for d in all_detected:
            key = (d["attack_type"], d["pattern"])
            if key not in seen:
                seen.add(key)
                unique_detected.append(d)
        
        confidence = self._calculate_confidence(unique_detected, decoded_versions)
        
        is_attack = confidence >= self.confidence_threshold_low
        attack_types = list(set(d["attack_type"] for d in unique_detected))
        severity = self._determine_severity(attack_types) if is_attack else Severity.LOW.value
        
        result = DetectionResult(
            is_attack=is_attack,
            attack_type=attack_types[0] if attack_types else "",
            confidence=confidence,
            detected_patterns=[d["matched_text"] or d["pattern"] for d in unique_detected],
            severity=severity,
            suggestion=self._get_suggestion(severity, attack_types),
            raw_input=user_input,
        )
        
        if is_attack:
            self.stats["attacks_detected"] += 1
            for at in attack_types:
                self.stats["attacks_by_type"][at] += 1
            self.stats["attacks_by_severity"][severity] += 1
        
        self.detection_history.append(result)
        
        if session_id:
            self.conversation_contexts[session_id].append(user_input)
        
        return result
    
    def _get_suggestion(self, severity: str, attack_types: List[str]) -> str:
        if severity == Severity.HIGH.value:
            return "拦截并返回安全提示"
        elif severity == Severity.MEDIUM.value:
            return "标记为可疑，需人工确认"
        else:
            return "记录观察"
    
    async def check_consistency(
        self,
        current_input: str,
        session_id: str,
    ) -> Dict:
        history = self.conversation_contexts.get(session_id, [])
        
        if len(history) < 2:
            return {"consistent": True, "reason": "历史记录不足"}
        
        sudden_topic_change = self._detect_sudden_change(current_input, history)
        
        return {
            "consistent": not sudden_topic_change,
            "reason": "检测到话题突变" if sudden_topic_change else "对话逻辑一致",
            "history_length": len(history),
        }
    
    def _detect_sudden_change(self, current: str, history: List[str]) -> bool:
        sensitive_keywords = ["密码", "转账", "验证码", "身份证", "银行卡"]
        
        current_lower = current.lower()
        has_sensitive = any(kw in current_lower for kw in sensitive_keywords)
        
        history_text = " ".join(history[-5:]).lower()
        history_has_sensitive = any(kw in history_text for kw in sensitive_keywords)
        
        if has_sensitive and not history_has_sensitive:
            return True
        
        return False
    
    async def report_false_positive(self, detection_id: str) -> bool:
        self.stats["false_positives"] += 1
        return True
    
    async def get_attack_statistics(self) -> Dict:
        return {
            "total_detections": self.stats["total_detections"],
            "attacks_detected": self.stats["attacks_detected"],
            "detection_rate": self.stats["attacks_detected"] / max(1, self.stats["total_detections"]),
            "attacks_by_type": dict(self.stats["attacks_by_type"]),
            "attacks_by_severity": dict(self.stats["attacks_by_severity"]),
            "false_positives": self.stats["false_positives"],
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_detections": self.stats["total_detections"],
            "attacks_detected": self.stats["attacks_detected"],
            "attacks_by_type": dict(self.stats["attacks_by_type"]),
            "attacks_by_severity": dict(self.stats["attacks_by_severity"]),
        }
