"""
免责声明系统
Disclaimer System

实现智能体输出的免责声明自动注入和管理
"""

import asyncio
import json
import uuid
import time
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


class DisclaimerType(Enum):
    BASIC = "DISCLAIMER_BASIC"
    VALUATION = "DISCLAIMER_VALUATION"
    INVESTMENT = "DISCLAIMER_INVESTMENT"
    TRANSACTION = "DISCLAIMER_TRANSACTION"
    GOV = "DISCLAIMER_GOV"
    EDU = "DISCLAIMER_EDU"
    REPORT = "DISCLAIMER_REPORT"
    CONSULTATION = "DISCLAIMER_CONSULTATION"


class DisplayPosition(Enum):
    BOTTOM = "bottom"
    SIDEBAR = "sidebar"
    POPUP = "popup"
    INLINE = "inline"
    FOOTER = "footer"


class OutputFormat(Enum):
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


DEFAULT_TEMPLATES = {
    DisclaimerType.BASIC: {
        "title": "免责声明",
        "content": "本平台提供的所有信息仅供参考，不构成任何投资建议。用户应自行核实数据准确性，并承担相应风险。",
        "position": DisplayPosition.BOTTOM,
        "force_display": True,
    },
    DisclaimerType.VALUATION: {
        "title": "估价免责声明",
        "content": "本估价结果基于历史数据和统计模型生成，存在一定误差，不构成实际成交依据。具体交易价格请以双方协商为准。",
        "position": DisplayPosition.FOOTER,
        "force_display": True,
    },
    DisclaimerType.INVESTMENT: {
        "title": "投资风险提示",
        "content": "本分析包含未来预测，存在不确定性。任何投资决策请咨询专业顾问，平台不对投资损失负责。",
        "position": DisplayPosition.POPUP,
        "force_display": True,
        "require_confirmation": True,
    },
    DisclaimerType.TRANSACTION: {
        "title": "交易辅助免责声明",
        "content": "本交易辅助信息仅供参考，平台不参与实际交易，不对交易纠纷负责。请仔细核对合同条款，建议咨询专业律师。",
        "position": DisplayPosition.BOTTOM,
        "force_display": True,
        "require_confirmation": True,
    },
    DisclaimerType.GOV: {
        "title": "政府数据免责声明",
        "content": "本数据仅供内部参考，不构成行政指令。具体政策执行请以官方文件为准。",
        "position": DisplayPosition.INLINE,
        "force_display": True,
    },
    DisclaimerType.EDU: {
        "title": "教学案例免责声明",
        "content": "本案例已脱敏处理，仅用于教学目的，不代表真实市场情况。",
        "position": DisplayPosition.BOTTOM,
        "force_display": True,
    },
    DisclaimerType.REPORT: {
        "title": "报告免责声明",
        "content": "本报告基于公开数据和分析模型生成，仅供参考。报告中的预测和结论不构成任何决策依据。",
        "position": DisplayPosition.FOOTER,
        "force_display": True,
    },
    DisclaimerType.CONSULTATION: {
        "title": "咨询免责声明",
        "content": "本咨询回复由AI生成，仅供参考。如需专业建议，请咨询相关领域专家。",
        "position": DisplayPosition.BOTTOM,
        "force_display": True,
    },
}


@dataclass
class DisclaimerTemplate:
    template_id: str
    disclaimer_type: DisclaimerType
    title: str
    content: str
    position: DisplayPosition = DisplayPosition.BOTTOM
    force_display: bool = True
    require_confirmation: bool = False
    version: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    applicable_ends: List[str] = field(default_factory=list)
    applicable_scenarios: List[str] = field(default_factory=list)
    language: str = "zh_CN"
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "disclaimer_type": self.disclaimer_type.value,
            "title": self.title,
            "content": self.content,
            "position": self.position.value,
            "force_display": self.force_display,
            "require_confirmation": self.require_confirmation,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "applicable_ends": self.applicable_ends,
            "applicable_scenarios": self.applicable_scenarios,
            "language": self.language,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisclaimerTemplate":
        return cls(
            template_id=data["template_id"],
            disclaimer_type=DisclaimerType(data["disclaimer_type"]),
            title=data["title"],
            content=data["content"],
            position=DisplayPosition(data.get("position", "bottom")),
            force_display=data.get("force_display", True),
            require_confirmation=data.get("require_confirmation", False),
            version=data.get("version", 1),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            applicable_ends=data.get("applicable_ends", []),
            applicable_scenarios=data.get("applicable_scenarios", []),
            language=data.get("language", "zh_CN"),
            is_active=data.get("is_active", True),
        )
    
    def render(self, format: OutputFormat = OutputFormat.TEXT) -> str:
        if format == OutputFormat.HTML:
            return f"""
<div class="disclaimer" data-template-id="{self.template_id}" data-position="{self.position.value}">
    <div class="disclaimer-title">{self.title}</div>
    <div class="disclaimer-content">{self.content}</div>
</div>
"""
        elif format == OutputFormat.MARKDOWN:
            return f"\n---\n**{self.title}**: {self.content}\n"
        elif format == OutputFormat.JSON:
            return json.dumps({
                "_disclaimer": {
                    "template_id": self.template_id,
                    "title": self.title,
                    "content": self.content,
                    "position": self.position.value,
                }
            }, ensure_ascii=False)
        else:
            return f"\n【{self.title}】{self.content}"


@dataclass
class ConsentRecord:
    consent_id: str
    user_id: str
    template_id: str
    disclaimer_type: DisclaimerType
    confirmed_at: float = field(default_factory=time.time)
    ip_address: str = ""
    device_fingerprint: str = ""
    user_agent: str = ""
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "disclaimer_type": self.disclaimer_type.value,
            "confirmed_at": self.confirmed_at,
            "ip_address": self.ip_address,
            "device_fingerprint": self.device_fingerprint,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "signature": self.signature,
        }
    
    def compute_signature(self) -> str:
        data = f"{self.user_id}{self.template_id}{self.confirmed_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class DisclaimerInjector:
    def __init__(self, disclaimer_system: "DisclaimerSystem"):
        self.disclaimer_system = disclaimer_system
    
    def inject(self, disclaimer_type: DisclaimerType, 
               output: Any, 
               format: OutputFormat = OutputFormat.TEXT,
               position: str = None) -> Any:
        template = self.disclaimer_system.get_template(disclaimer_type)
        if not template:
            return output
        
        disclaimer_text = template.render(format)
        
        if format == OutputFormat.JSON:
            if isinstance(output, dict):
                result = output.copy()
                disclaimer_data = {
                    "_disclaimer": {
                        "template_id": template.template_id,
                        "title": template.title,
                        "content": template.content,
                        "position": template.position.value,
                        "force_display": template.force_display,
                    }
                }
                result.update(disclaimer_data)
                return result
            else:
                return output
        
        if isinstance(output, str):
            if position == "top":
                return disclaimer_text + output
            else:
                return output + disclaimer_text
        
        if isinstance(output, dict):
            output["_disclaimer"] = {
                "template_id": template.template_id,
                "title": template.title,
                "content": template.content,
                "position": template.position.value,
            }
            return output
        
        return output


def inject_disclaimer(disclaimer_type: DisclaimerType, 
                      position: str = "bottom",
                      format: OutputFormat = OutputFormat.TEXT):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            if hasattr(self, "_disclaimer_injector"):
                return self._disclaimer_injector.inject(disclaimer_type, result, format, position)
            return result
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if hasattr(self, "_disclaimer_injector"):
                return self._disclaimer_injector.inject(disclaimer_type, result, format, position)
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class ConsentManager:
    def __init__(self, hippocampus: Optional[Any] = None):
        self.hippocampus = hippocampus
        self._consents: Dict[str, ConsentRecord] = {}
        self._user_consents: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()
    
    async def record_consent(self, user_id: str, template_id: str,
                              disclaimer_type: DisclaimerType,
                              ip_address: str = "",
                              device_fingerprint: str = "",
                              user_agent: str = "",
                              session_id: str = "",
                              metadata: Dict[str, Any] = None) -> str:
        async with self._lock:
            consent = ConsentRecord(
                consent_id=str(uuid.uuid4()),
                user_id=user_id,
                template_id=template_id,
                disclaimer_type=disclaimer_type,
                ip_address=ip_address,
                device_fingerprint=device_fingerprint,
                user_agent=user_agent,
                session_id=session_id,
                metadata=metadata or {},
            )
            consent.signature = consent.compute_signature()
            
            self._consents[consent.consent_id] = consent
            self._user_consents[user_id].add(consent.consent_id)
            
            if self.hippocampus:
                await self._store_in_hippocampus(consent)
            
            logger.info(f"Consent recorded: {consent.consent_id} for user {user_id}")
            return consent.consent_id
    
    async def has_consented(self, user_id: str, disclaimer_type: DisclaimerType,
                            within_days: int = 365) -> bool:
        cutoff_time = time.time() - (within_days * 86400)
        
        for consent_id in self._user_consents.get(user_id, []):
            consent = self._consents.get(consent_id)
            if consent and consent.disclaimer_type == disclaimer_type:
                if consent.confirmed_at >= cutoff_time:
                    return True
        
        return False
    
    async def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        consent_ids = self._user_consents.get(user_id, [])
        return [self._consents[cid] for cid in consent_ids if cid in self._consents]
    
    async def get_recent_consent(self, user_id: str, 
                                  disclaimer_type: DisclaimerType) -> Optional[ConsentRecord]:
        consents = await self.get_user_consents(user_id)
        type_consents = [c for c in consents if c.disclaimer_type == disclaimer_type]
        
        if not type_consents:
            return None
        
        return max(type_consents, key=lambda c: c.confirmed_at)
    
    async def _store_in_hippocampus(self, consent: ConsentRecord) -> None:
        if not self.hippocampus:
            return
        
        try:
            await self.hippocampus.store_memory(
                content=json.dumps(consent.to_dict()),
                memory_type="disclaimer_consent",
                source_end="system",
                tags=["disclaimer", "consent", consent.disclaimer_type.value],
            )
        except Exception as e:
            logger.error(f"Failed to store consent in hippocampus: {e}")


class DisclaimerSystem:
    def __init__(self, hippocampus: Optional[Any] = None,
                 message_bus: Optional[Any] = None):
        self.hippocampus = hippocampus
        self.message_bus = message_bus
        
        self._templates: Dict[str, DisclaimerTemplate] = {}
        self._type_templates: Dict[DisclaimerType, str] = {}
        
        self.injector = DisclaimerInjector(self)
        self.consent_manager = ConsentManager(hippocampus)
        
        self._lock = asyncio.Lock()
        self._operation_log: List[Dict[str, Any]] = []
        
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        for dtype, defaults in DEFAULT_TEMPLATES.items():
            template = DisclaimerTemplate(
                template_id=f"tpl_{dtype.value.lower()}",
                disclaimer_type=dtype,
                title=defaults["title"],
                content=defaults["content"],
                position=defaults.get("position", DisplayPosition.BOTTOM),
                force_display=defaults.get("force_display", True),
                require_confirmation=defaults.get("require_confirmation", False),
                applicable_ends=[],
                applicable_scenarios=[],
            )
            self._templates[template.template_id] = template
            self._type_templates[dtype] = template.template_id
    
    async def create_template(self, disclaimer_type: DisclaimerType,
                               title: str, content: str,
                               position: DisplayPosition = DisplayPosition.BOTTOM,
                               force_display: bool = True,
                               require_confirmation: bool = False,
                               applicable_ends: List[str] = None,
                               applicable_scenarios: List[str] = None,
                               language: str = "zh_CN") -> str:
        async with self._lock:
            template_id = f"tpl_{str(uuid.uuid4())[:8]}"
            
            template = DisclaimerTemplate(
                template_id=template_id,
                disclaimer_type=disclaimer_type,
                title=title,
                content=content,
                position=position,
                force_display=force_display,
                require_confirmation=require_confirmation,
                applicable_ends=applicable_ends or [],
                applicable_scenarios=applicable_scenarios or [],
                language=language,
            )
            
            self._templates[template_id] = template
            self._type_templates[disclaimer_type] = template_id
            
            self._log_operation("create_template", template)
            
            logger.info(f"Template {template_id} created")
            return template_id
    
    async def update_template(self, template_id: str, **kwargs) -> bool:
        async with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return False
            
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = time.time()
            template.version += 1
            
            self._log_operation("update_template", template)
            
            return True
    
    async def delete_template(self, template_id: str) -> bool:
        async with self._lock:
            template = self._templates.pop(template_id, None)
            if not template:
                return False
            
            if self._type_templates.get(template.disclaimer_type) == template_id:
                del self._type_templates[template.disclaimer_type]
            
            self._log_operation("delete_template", template)
            
            return True
    
    def get_template(self, disclaimer_type: DisclaimerType) -> Optional[DisclaimerTemplate]:
        template_id = self._type_templates.get(disclaimer_type)
        if template_id:
            return self._templates.get(template_id)
        return None
    
    def get_template_by_id(self, template_id: str) -> Optional[DisclaimerTemplate]:
        return self._templates.get(template_id)
    
    def get_all_templates(self) -> List[DisclaimerTemplate]:
        return list(self._templates.values())
    
    def get_templates_for_end(self, end_type: str) -> List[DisclaimerTemplate]:
        return [
            t for t in self._templates.values()
            if not t.applicable_ends or end_type in t.applicable_ends
        ]
    
    async def inject_disclaimer(self, output: Any, 
                                 disclaimer_type: DisclaimerType,
                                 format: OutputFormat = OutputFormat.TEXT,
                                 position: str = None) -> Any:
        return self.injector.inject(disclaimer_type, output, format, position)
    
    async def check_confirmation_required(self, user_id: str,
                                           disclaimer_type: DisclaimerType,
                                           within_days: int = 365) -> bool:
        template = self.get_template(disclaimer_type)
        if not template or not template.require_confirmation:
            return False
        
        has_consented = await self.consent_manager.has_consented(
            user_id, disclaimer_type, within_days
        )
        
        return not has_consented
    
    async def record_user_consent(self, user_id: str, disclaimer_type: DisclaimerType,
                                   ip_address: str = "",
                                   device_fingerprint: str = "",
                                   user_agent: str = "",
                                   session_id: str = "") -> str:
        template = self.get_template(disclaimer_type)
        if not template:
            raise ValueError(f"No template found for {disclaimer_type}")
        
        consent_id = await self.consent_manager.record_consent(
            user_id=user_id,
            template_id=template.template_id,
            disclaimer_type=disclaimer_type,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            user_agent=user_agent,
            session_id=session_id,
        )
        
        if self.message_bus:
            await self._broadcast_consent(user_id, disclaimer_type, consent_id)
        
        return consent_id
    
    async def get_user_consent_history(self, user_id: str) -> List[ConsentRecord]:
        return await self.consent_manager.get_user_consents(user_id)
    
    async def verify_consent(self, consent_id: str) -> bool:
        consent = self.consent_manager._consents.get(consent_id)
        if not consent:
            return False
        
        expected_signature = consent.compute_signature()
        return consent.signature == expected_signature
    
    async def _broadcast_consent(self, user_id: str, disclaimer_type: DisclaimerType,
                                  consent_id: str) -> None:
        if not self.message_bus:
            return
        
        try:
            from .five_end_bus import EventType, CrossEndEvent, EndType, MessagePriority
            
            event = CrossEndEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.DISCLAIMER_CONFIRMED,
                source_end=EndType.GOV,
                source_agent="disclaimer_system",
                broadcast=True,
                payload={
                    "user_id": user_id,
                    "disclaimer_type": disclaimer_type.value,
                    "consent_id": consent_id,
                    "timestamp": time.time(),
                },
                priority=MessagePriority.NORMAL,
            )
            await self.message_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to broadcast consent: {e}")
    
    def _log_operation(self, operation: str, template: DisclaimerTemplate) -> None:
        self._operation_log.append({
            "timestamp": time.time(),
            "operation": operation,
            "template_id": template.template_id,
            "disclaimer_type": template.disclaimer_type.value,
        })
    
    async def get_operation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._operation_log[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        total_consents = len(self.consent_manager._consents)
        
        by_type = defaultdict(int)
        for consent in self.consent_manager._consents.values():
            by_type[consent.disclaimer_type.value] += 1
        
        return {
            "total_templates": len(self._templates),
            "total_consents": total_consents,
            "consents_by_type": dict(by_type),
            "templates_requiring_confirmation": sum(
                1 for t in self._templates.values() if t.require_confirmation
            ),
        }


class DisclaimerMonitor:
    def __init__(self, disclaimer_system: DisclaimerSystem):
        self.disclaimer_system = disclaimer_system
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.disclaimer_system.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_consent_rate(self, disclaimer_type: DisclaimerType) -> float:
        stats = await self.disclaimer_system.get_statistics()
        total = stats["total_consents"]
        
        if total == 0:
            return 0
        
        by_type = stats["consents_by_type"]
        type_count = by_type.get(disclaimer_type.value, 0)
        
        return type_count / total
    
    async def get_template_usage(self) -> Dict[str, int]:
        usage = defaultdict(int)
        
        for consent in self.disclaimer_system.consent_manager._consents.values():
            usage[consent.template_id] += 1
        
        return dict(usage)
