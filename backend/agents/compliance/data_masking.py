"""
数据脱敏智能体
对敏感数据进行脱敏处理
"""
import asyncio
import hashlib
import json
import logging
import random
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MaskingStrategy(str, Enum):
    REDACT = "redact"
    HASH = "hash"
    MASK = "mask"
    GENERALIZE = "generalize"
    PERTURB = "perturb"
    SUBSTITUTE = "substitute"
    ENCRYPT = "encrypt"


class MaskingScope(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    CONTEXTUAL = "contextual"


class MaskingRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    data_type: str
    strategy: MaskingStrategy
    scope: MaskingScope = MaskingScope.PARTIAL
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class MaskingResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid4()))
    original_length: int
    masked_length: int
    fields_masked: int = 0
    fields_by_type: Dict[str, int] = Field(default_factory=dict)
    strategy_used: Dict[str, str] = Field(default_factory=dict)
    masked_data: Dict[str, Any]
    masking_map: Dict[str, str] = Field(default_factory=dict)
    processed_at: datetime = Field(default_factory=datetime.now)


class MaskingContext(BaseModel):
    user_role: Optional[str] = None
    purpose: Optional[str] = None
    retention_days: Optional[int] = None
    audit_required: bool = True


class DataMasker:
    def __init__(self, salt: str = "fangdudu_masking_salt"):
        self.salt = salt
    
    def redact(self, value: str) -> str:
        return "[REDACTED]"
    
    def hash(self, value: str, algorithm: str = "sha256") -> str:
        if algorithm == "sha256":
            hashed = hashlib.sha256(f"{self.salt}{value}".encode()).hexdigest()
        elif algorithm == "md5":
            hashed = hashlib.md5(f"{self.salt}{value}".encode()).hexdigest()
        else:
            hashed = hashlib.sha256(f"{self.salt}{value}".encode()).hexdigest()
        
        return f"[HASH:{hashed[:16]}]"
    
    def mask(
        self,
        value: str,
        mask_char: str = "*",
        visible_start: int = 2,
        visible_end: int = 2
    ) -> str:
        if len(value) <= visible_start + visible_end:
            return mask_char * len(value)
        
        masked_length = len(value) - visible_start - visible_end
        return value[:visible_start] + mask_char * masked_length + value[-visible_end:]
    
    def mask_phone(self, phone: str) -> str:
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) == 11:
            return cleaned[:3] + "****" + cleaned[-4:]
        return self.mask(phone)
    
    def mask_id_card(self, id_card: str) -> str:
        cleaned = re.sub(r'\s', '', id_card)
        if len(cleaned) == 18:
            return cleaned[:6] + "********" + cleaned[-4:]
        return self.mask(id_card)
    
    def mask_email(self, email: str) -> str:
        if '@' in email:
            parts = email.split('@')
            if len(parts[0]) <= 2:
                return "*" * len(parts[0]) + "@" + parts[1]
            return parts[0][:2] + "***@" + parts[1]
        return self.mask(email)
    
    def mask_bank_account(self, account: str) -> str:
        cleaned = re.sub(r'\s', '', account)
        return "**** **** **** " + cleaned[-4:]
    
    def generalize(self, value: str, data_type: str) -> str:
        if data_type == "address":
            match = re.match(r'([\u4e00-\u9fa5]+省)([\u4e00-\u9fa5]+市)', value)
            if match:
                return f"{match.group(1)}{match.group(2)}[某区]"
        
        elif data_type == "age":
            try:
                age = int(value)
                if age < 18:
                    return "未成年"
                elif age < 30:
                    return "青年"
                elif age < 50:
                    return "中年"
                else:
                    return "老年"
            except ValueError:
                pass
        
        elif data_type == "income":
            try:
                income = float(value)
                if income < 5000:
                    return "低收入"
                elif income < 10000:
                    return "中等收入"
                elif income < 20000:
                    return "较高收入"
                else:
                    return "高收入"
            except ValueError:
                pass
        
        return "[GENERALIZED]"
    
    def perturb(
        self,
        value: Union[int, float],
        noise_range: float = 0.1
    ) -> Union[int, float]:
        if isinstance(value, int):
            noise = int(value * noise_range * random.uniform(-1, 1))
            return value + noise
        else:
            noise = value * noise_range * random.uniform(-1, 1)
            return round(value + noise, 2)
    
    def substitute(self, value: str, data_type: str) -> str:
        substitutions = {
            "name": ["张三", "李四", "王五"],
            "phone": ["13800138000", "13900139000"],
            "email": ["test@example.com", "user@example.com"],
            "address": ["北京市朝阳区某街道", "上海市浦东新区某路"],
        }
        
        if data_type in substitutions:
            return random.choice(substitutions[data_type])
        
        return "[SUBSTITUTED]"


class RuleEngine:
    DEFAULT_RULES = [
        MaskingRule(
            name="身份证脱敏",
            data_type="id_card_cn",
            strategy=MaskingStrategy.MASK,
            parameters={"visible_start": 6, "visible_end": 4},
            priority=10
        ),
        MaskingRule(
            name="手机号脱敏",
            data_type="phone_cn",
            strategy=MaskingStrategy.MASK,
            parameters={"visible_start": 3, "visible_end": 4},
            priority=10
        ),
        MaskingRule(
            name="邮箱脱敏",
            data_type="email",
            strategy=MaskingStrategy.MASK,
            parameters={},
            priority=8
        ),
        MaskingRule(
            name="银行卡脱敏",
            data_type="bank_account",
            strategy=MaskingStrategy.MASK,
            parameters={"visible_end": 4},
            priority=10
        ),
        MaskingRule(
            name="密码完全遮蔽",
            data_type="password",
            strategy=MaskingStrategy.REDACT,
            parameters={},
            priority=20
        ),
        MaskingRule(
            name="API密钥哈希",
            data_type="api_key",
            strategy=MaskingStrategy.HASH,
            parameters={"algorithm": "sha256"},
            priority=15
        ),
        MaskingRule(
            name="地址泛化",
            data_type="address",
            strategy=MaskingStrategy.GENERALIZE,
            parameters={},
            priority=5
        ),
        MaskingRule(
            name="收入扰动",
            data_type="income",
            strategy=MaskingStrategy.PERTURB,
            parameters={"noise_range": 0.1},
            priority=5
        ),
    ]
    
    def __init__(self):
        self.rules: Dict[str, MaskingRule] = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        for rule in self.DEFAULT_RULES:
            self.rules[rule.rule_id] = rule
    
    def add_rule(self, rule: MaskingRule):
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def get_applicable_rules(
        self,
        data_type: str,
        context: Optional[MaskingContext] = None
    ) -> List[MaskingRule]:
        applicable = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if rule.data_type == data_type or rule.data_type == "*":
                applicable.append(rule)
        
        applicable.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable


class DataMaskingAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "DataMasking",
        audit_agent: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.audit_agent = audit_agent
        
        self.masker = DataMasker()
        self.rule_engine = RuleEngine()
        
        self.masking_history: List[MaskingResult] = []
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"DataMaskingAgent {self.agent_id} initialized")
    
    async def mask_data(
        self,
        data: Dict[str, Any],
        context: Optional[MaskingContext] = None,
        field_rules: Optional[Dict[str, str]] = None
    ) -> MaskingResult:
        original_length = len(json.dumps(data, ensure_ascii=False))
        
        masked_data = {}
        fields_masked = 0
        fields_by_type: Dict[str, int] = {}
        strategy_used: Dict[str, str] = {}
        masking_map: Dict[str, str] = {}
        
        for field_name, field_value in data.items():
            if field_value is None:
                masked_data[field_name] = None
                continue
            
            if isinstance(field_value, dict):
                nested_result = await self.mask_data(field_value, context)
                masked_data[field_name] = nested_result.masked_data
                fields_masked += nested_result.fields_masked
                continue
            
            if isinstance(field_value, list):
                masked_list = []
                for item in field_value:
                    if isinstance(item, dict):
                        nested_result = await self.mask_data(item, context)
                        masked_list.append(nested_result.masked_data)
                        fields_masked += nested_result.fields_masked
                    else:
                        masked_list.append(item)
                masked_data[field_name] = masked_list
                continue
            
            data_type = self._infer_data_type(field_name, field_value)
            
            if field_rules and field_name in field_rules:
                data_type = field_rules[field_name]
            
            rules = self.rule_engine.get_applicable_rules(data_type, context)
            
            if rules:
                rule = rules[0]
                masked_value = self._apply_rule(field_value, rule)
                
                if masked_value != str(field_value):
                    fields_masked += 1
                    fields_by_type[data_type] = fields_by_type.get(data_type, 0) + 1
                    strategy_used[field_name] = rule.strategy.value
                    masking_map[field_name] = f"{data_type}:{rule.strategy.value}"
                
                masked_data[field_name] = masked_value
            else:
                masked_data[field_name] = field_value
        
        masked_length = len(json.dumps(masked_data, ensure_ascii=False))
        
        result = MaskingResult(
            original_length=original_length,
            masked_length=masked_length,
            fields_masked=fields_masked,
            fields_by_type=fields_by_type,
            strategy_used=strategy_used,
            masked_data=masked_data,
            masking_map=masking_map
        )
        
        self.masking_history.append(result)
        
        if self.audit_agent and context and context.audit_required:
            await self.audit_agent.log_data_access(
                user_id=context.user_role or "system",
                resource="data_masking",
                resource_type="masking_operation",
                action="mask",
                details={
                    "fields_masked": fields_masked,
                    "strategies_used": list(strategy_used.values())
                }
            )
        
        return result
    
    def _infer_data_type(self, field_name: str, value: Any) -> str:
        field_lower = field_name.lower()
        
        if isinstance(value, str):
            if re.match(r'^\d{17}[\dXx]$', value):
                return "id_card_cn"
            if re.match(r'^1[3-9]\d{9}$', value):
                return "phone_cn"
            if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
                return "email"
            if re.match(r'^\d{16,19}$', value):
                return "bank_account"
        
        if 'password' in field_lower or 'pwd' in field_lower:
            return "password"
        if 'phone' in field_lower or 'mobile' in field_lower or 'tel' in field_lower:
            return "phone_cn"
        if 'email' in field_lower or 'mail' in field_lower:
            return "email"
        if 'id_card' in field_lower or 'idcard' in field_lower:
            return "id_card_cn"
        if 'bank' in field_lower or 'account' in field_lower:
            return "bank_account"
        if 'api_key' in field_lower or 'apikey' in field_lower:
            return "api_key"
        if 'address' in field_lower or 'addr' in field_lower:
            return "address"
        if 'income' in field_lower or 'salary' in field_lower:
            return "income"
        if 'name' in field_lower:
            return "name"
        
        return "unknown"
    
    def _apply_rule(self, value: Any, rule: MaskingRule) -> Any:
        if not isinstance(value, (str, int, float)):
            return value
        
        str_value = str(value)
        
        if rule.strategy == MaskingStrategy.REDACT:
            return self.masker.redact(str_value)
        
        elif rule.strategy == MaskingStrategy.HASH:
            algorithm = rule.parameters.get("algorithm", "sha256")
            return self.masker.hash(str_value, algorithm)
        
        elif rule.strategy == MaskingStrategy.MASK:
            data_type = rule.data_type
            
            if data_type == "phone_cn":
                return self.masker.mask_phone(str_value)
            elif data_type == "id_card_cn":
                return self.masker.mask_id_card(str_value)
            elif data_type == "email":
                return self.masker.mask_email(str_value)
            elif data_type == "bank_account":
                return self.masker.mask_bank_account(str_value)
            else:
                visible_start = rule.parameters.get("visible_start", 2)
                visible_end = rule.parameters.get("visible_end", 2)
                return self.masker.mask(str_value, "*", visible_start, visible_end)
        
        elif rule.strategy == MaskingStrategy.GENERALIZE:
            return self.masker.generalize(str_value, rule.data_type)
        
        elif rule.strategy == MaskingStrategy.PERTURB:
            try:
                num_value = float(value) if isinstance(value, str) else value
                noise_range = rule.parameters.get("noise_range", 0.1)
                return self.masker.perturb(num_value, noise_range)
            except (ValueError, TypeError):
                return str_value
        
        elif rule.strategy == MaskingStrategy.SUBSTITUTE:
            return self.masker.substitute(str_value, rule.data_type)
        
        return str_value
    
    async def mask_field(
        self,
        value: Any,
        data_type: str,
        strategy: Optional[MaskingStrategy] = None
    ) -> Any:
        if strategy:
            rule = MaskingRule(
                name="ad_hoc",
                data_type=data_type,
                strategy=strategy
            )
        else:
            rules = self.rule_engine.get_applicable_rules(data_type)
            if not rules:
                return value
            rule = rules[0]
        
        return self._apply_rule(value, rule)
    
    async def mask_text(
        self,
        text: str,
        patterns: Optional[Dict[str, str]] = None
    ) -> Tuple[str, Dict[str, int]]:
        if not patterns:
            patterns = {
                r'\b\d{17}[\dXx]\b': 'id_card_cn',
                r'\b1[3-9]\d{9}\b': 'phone_cn',
                r'\b[\w\.-]+@[\w\.-]+\.\w+\b': 'email',
            }
        
        masked_text = text
        counts: Dict[str, int] = {}
        
        for pattern, data_type in patterns.items():
            matches = list(re.finditer(pattern, text))
            
            for match in reversed(matches):
                original = match.group()
                masked = await self.mask_field(original, data_type)
                masked_text = masked_text[:match.start()] + masked + masked_text[match.end():]
                counts[data_type] = counts.get(data_type, 0) + 1
        
        return masked_text, counts
    
    def add_masking_rule(self, rule: MaskingRule):
        self.rule_engine.add_rule(rule)
        self.logger.info(f"Added masking rule: {rule.name}")
    
    def remove_masking_rule(self, rule_id: str) -> bool:
        success = self.rule_engine.remove_rule(rule_id)
        if success:
            self.logger.info(f"Removed masking rule: {rule_id}")
        return success
    
    async def get_masking_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        return [
            {
                "result_id": r.result_id,
                "original_length": r.original_length,
                "masked_length": r.masked_length,
                "fields_masked": r.fields_masked,
                "fields_by_type": r.fields_by_type,
                "processed_at": r.processed_at.isoformat()
            }
            for r in self.masking_history[-limit:]
        ]
    
    async def get_statistics(self) -> Dict[str, Any]:
        total_operations = len(self.masking_history)
        total_fields_masked = sum(r.fields_masked for r in self.masking_history)
        
        all_by_type: Dict[str, int] = {}
        for result in self.masking_history:
            for data_type, count in result.fields_by_type.items():
                all_by_type[data_type] = all_by_type.get(data_type, 0) + count
        
        return {
            "total_operations": total_operations,
            "total_fields_masked": total_fields_masked,
            "fields_by_type": all_by_type,
            "rules_count": len(self.rule_engine.rules)
        }
