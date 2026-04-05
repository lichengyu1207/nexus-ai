"""
敏感数据识别智能体
自动识别文本中的敏感数据
"""
import asyncio
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class DataType(str, Enum):
    ID_CARD_CN = "id_card_cn"
    PHONE_CN = "phone_cn"
    EMAIL = "email"
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    PASSPORT = "passport"
    ADDRESS = "address"
    NAME = "name"
    PASSWORD = "password"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    LICENSE_PLATE = "license_plate"
    SOCIAL_SECURITY = "social_security"
    MEDICAL_RECORD = "medical_record"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC = "biometric"
    LOCATION = "location"


class SensitiveDataRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid4()))
    data_type: DataType
    sensitivity_level: SensitivityLevel
    original_text: str
    masked_text: str
    position: Tuple[int, int]
    confidence: float
    context: str = ""
    detected_at: datetime = Field(default_factory=datetime.now)


class DetectionResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    total_findings: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_level: Dict[str, int] = Field(default_factory=dict)
    records: List[SensitiveDataRecord] = Field(default_factory=list)
    risk_score: float = 0.0
    scanned_at: datetime = Field(default_factory=datetime.now)


class SensitivePattern:
    PATTERNS = {
        DataType.ID_CARD_CN: {
            "pattern": r'\b\d{17}[\dXx]\b',
            "level": SensitivityLevel.CONFIDENTIAL,
            "description": "中国身份证号",
            "validation": lambda x: True
        },
        DataType.PHONE_CN: {
            "pattern": r'\b1[3-9]\d{9}\b',
            "level": SensitivityLevel.CONFIDENTIAL,
            "description": "中国手机号",
            "validation": lambda x: len(x) == 11
        },
        DataType.EMAIL: {
            "pattern": r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b',
            "level": SensitivityLevel.INTERNAL,
            "description": "电子邮箱",
            "validation": lambda x: '@' in x
        },
        DataType.BANK_ACCOUNT: {
            "pattern": r'\b\d{16,19}\b',
            "level": SensitivityLevel.SECRET,
            "description": "银行账号",
            "validation": lambda x: 16 <= len(x) <= 19
        },
        DataType.CREDIT_CARD: {
            "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "level": SensitivityLevel.SECRET,
            "description": "信用卡号",
            "validation": lambda x: True
        },
        DataType.PASSPORT: {
            "pattern": r'\b[A-Z]{1,2}\d{6,9}\b',
            "level": SensitivityLevel.CONFIDENTIAL,
            "description": "护照号",
            "validation": lambda x: True
        },
        DataType.PASSWORD: {
            "pattern": r'(?:password|passwd|pwd|密码)[\s:=]+["\']?[\w@#$%^&*()]+["\']?',
            "level": SensitivityLevel.SECRET,
            "description": "密码",
            "validation": lambda x: True
        },
        DataType.API_KEY: {
            "pattern": r'(?:api[_-]?key|apikey|secret[_-]?key)[\s:=]+["\']?[a-zA-Z0-9_-]{20,}["\']?',
            "level": SensitivityLevel.SECRET,
            "description": "API密钥",
            "validation": lambda x: len(x) >= 20
        },
        DataType.IP_ADDRESS: {
            "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "level": SensitivityLevel.INTERNAL,
            "description": "IP地址",
            "validation": lambda x: True
        },
        DataType.MAC_ADDRESS: {
            "pattern": r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
            "level": SensitivityLevel.INTERNAL,
            "description": "MAC地址",
            "validation": lambda x: True
        },
        DataType.LICENSE_PLATE: {
            "pattern": r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-HJ-NP-Z0-9]{5,6}',
            "level": SensitivityLevel.CONFIDENTIAL,
            "description": "车牌号",
            "validation": lambda x: True
        },
    }
    
    CONTEXT_PATTERNS = {
        DataType.NAME: [
            r'(?:姓名|名字|称呼)[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'(?:name)[：:]\s*([a-zA-Z\s]{2,20})',
        ],
        DataType.ADDRESS: [
            r'(?:地址|住址)[：:]\s*([\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+)',
            r'(?:address)[：:]\s*(.{10,100})',
        ],
        DataType.FINANCIAL_DATA: [
            r'(?:金额|价格|费用)[：:]\s*(\d+(?:\.\d{1,2})?)\s*(?:元|万元)?',
            r'(?:收入|工资|薪资)[：:]\s*(\d+(?:\.\d{1,2})?)',
        ],
    }


class ContextAnalyzer:
    SENSITIVE_CONTEXTS = [
        "个人信息", "隐私", "敏感", "机密", "保密",
        "身份证", "银行卡", "密码", "账户",
        "personal", "private", "secret", "confidential"
    ]
    
    NON_SENSITIVE_CONTEXTS = [
        "示例", "测试", "演示", "样例", "模板",
        "example", "test", "demo", "sample", "template"
    ]
    
    def analyze(self, text: str, position: Tuple[int, int], window: int = 50) -> Dict[str, Any]:
        start = max(0, position[0] - window)
        end = min(len(text), position[1] + window)
        
        context = text[start:end]
        
        is_sensitive = any(kw in context for kw in self.SENSITIVE_CONTEXTS)
        is_non_sensitive = any(kw in context for kw in self.NON_SENSITIVE_CONTEXTS)
        
        if is_non_sensitive:
            confidence_modifier = -0.3
        elif is_sensitive:
            confidence_modifier = 0.2
        else:
            confidence_modifier = 0.0
        
        return {
            "context": context,
            "is_sensitive_context": is_sensitive,
            "is_non_sensitive_context": is_non_sensitive,
            "confidence_modifier": confidence_modifier
        }


class SensitiveDataIdentifierAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "SensitiveDataIdentifier",
        llm_client: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.llm_client = llm_client
        
        self.patterns = SensitivePattern.PATTERNS
        self.context_patterns = SensitivePattern.CONTEXT_PATTERNS
        self.context_analyzer = ContextAnalyzer()
        
        self.detection_history: List[DetectionResult] = []
        self.custom_patterns: Dict[DataType, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"SensitiveDataIdentifierAgent {self.agent_id} initialized")
    
    async def scan(
        self,
        text: str,
        source_id: str,
        include_context: bool = True
    ) -> DetectionResult:
        records = []
        by_type: Dict[str, int] = {}
        by_level: Dict[str, int] = {}
        
        all_patterns = {**self.patterns, **self.custom_patterns}
        
        for data_type, pattern_config in all_patterns.items():
            pattern = pattern_config["pattern"]
            level = pattern_config["level"]
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                original = match.group()
                position = (match.start(), match.end())
                
                confidence = 0.8
                
                if include_context:
                    context_result = self.context_analyzer.analyze(text, position)
                    confidence += context_result["confidence_modifier"]
                    confidence = max(0.1, min(1.0, confidence))
                else:
                    context_result = {"context": ""}
                
                if pattern_config.get("validation"):
                    if not pattern_config["validation"](original):
                        continue
                
                masked = self._mask_data(original, data_type)
                
                record = SensitiveDataRecord(
                    data_type=data_type,
                    sensitivity_level=level,
                    original_text=original,
                    masked_text=masked,
                    position=position,
                    confidence=confidence,
                    context=context_result.get("context", "")
                )
                
                records.append(record)
                
                by_type[data_type.value] = by_type.get(data_type.value, 0) + 1
                by_level[level.value] = by_level.get(level.value, 0) + 1
        
        for data_type, patterns in self.context_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    original = match.group(1)
                    position = (match.start(1), match.end(1))
                    
                    record = SensitiveDataRecord(
                        data_type=data_type,
                        sensitivity_level=SensitivityLevel.CONFIDENTIAL,
                        original_text=original,
                        masked_text=self._mask_data(original, data_type),
                        position=position,
                        confidence=0.7,
                        context=text[max(0, position[0]-20):position[1]+20]
                    )
                    
                    records.append(record)
                    
                    by_type[data_type.value] = by_type.get(data_type.value, 0) + 1
                    by_level[SensitivityLevel.CONFIDENTIAL.value] = by_level.get(
                        SensitivityLevel.CONFIDENTIAL.value, 0
                    ) + 1
        
        risk_score = self._calculate_risk_score(records)
        
        result = DetectionResult(
            source_id=source_id,
            total_findings=len(records),
            by_type=by_type,
            by_level=by_level,
            records=records,
            risk_score=risk_score
        )
        
        self.detection_history.append(result)
        
        return result
    
    def _mask_data(self, data: str, data_type: DataType) -> str:
        if data_type == DataType.ID_CARD_CN:
            return data[:6] + "********" + data[-4:]
        elif data_type == DataType.PHONE_CN:
            return data[:3] + "****" + data[-4:]
        elif data_type == DataType.EMAIL:
            parts = data.split("@")
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
        elif data_type in [DataType.BANK_ACCOUNT, DataType.CREDIT_CARD]:
            return "**** **** **** " + data[-4:]
        elif data_type == DataType.NAME:
            if len(data) <= 2:
                return data[0] + "*"
            return data[0] + "*" * (len(data) - 2) + data[-1]
        elif data_type == DataType.PASSWORD:
            return "[REDACTED]"
        elif data_type == DataType.API_KEY:
            return data[:4] + "*" * (len(data) - 8) + data[-4:]
        
        if len(data) <= 4:
            return "****"
        return data[:2] + "*" * (len(data) - 4) + data[-2:]
    
    def _calculate_risk_score(self, records: List[SensitiveDataRecord]) -> float:
        if not records:
            return 0.0
        
        level_weights = {
            SensitivityLevel.PUBLIC: 0.1,
            SensitivityLevel.INTERNAL: 0.3,
            SensitivityLevel.CONFIDENTIAL: 0.6,
            SensitivityLevel.SECRET: 0.9,
            SensitivityLevel.TOP_SECRET: 1.0,
        }
        
        total_weight = sum(level_weights.get(r.sensitivity_level, 0.5) for r in records)
        
        avg_confidence = sum(r.confidence for r in records) / len(records)
        
        count_factor = min(1.0, len(records) / 20)
        
        risk_score = (total_weight / len(records)) * 0.5 + avg_confidence * 0.3 + count_factor * 0.2
        
        return min(1.0, risk_score)
    
    async def scan_batch(
        self,
        texts: List[Tuple[str, str]]
    ) -> List[DetectionResult]:
        results = []
        
        for text, source_id in texts:
            result = await self.scan(text, source_id)
            results.append(result)
        
        return results
    
    async def quick_check(self, text: str) -> bool:
        for data_type, pattern_config in self.patterns.items():
            if re.search(pattern_config["pattern"], text, re.IGNORECASE):
                return True
        
        return False
    
    async def get_sensitive_types(self, text: str) -> List[DataType]:
        found_types = []
        
        for data_type, pattern_config in self.patterns.items():
            if re.search(pattern_config["pattern"], text, re.IGNORECASE):
                found_types.append(data_type)
        
        return found_types
    
    def add_custom_pattern(
        self,
        data_type: DataType,
        pattern: str,
        level: SensitivityLevel,
        description: str = ""
    ):
        self.custom_patterns[data_type] = {
            "pattern": pattern,
            "level": level,
            "description": description,
            "validation": None
        }
        
        self.logger.info(f"Added custom pattern for {data_type.value}")
    
    def remove_custom_pattern(self, data_type: DataType) -> bool:
        if data_type in self.custom_patterns:
            del self.custom_patterns[data_type]
            return True
        return False
    
    async def get_detection_history(
        self,
        source_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        results = self.detection_history
        
        if source_id:
            results = [r for r in results if r.source_id == source_id]
        
        return [
            {
                "result_id": r.result_id,
                "source_id": r.source_id,
                "total_findings": r.total_findings,
                "by_type": r.by_type,
                "risk_score": r.risk_score,
                "scanned_at": r.scanned_at.isoformat()
            }
            for r in results[-limit:]
        ]
    
    async def get_statistics(self) -> Dict[str, Any]:
        total_scans = len(self.detection_history)
        total_findings = sum(r.total_findings for r in self.detection_history)
        
        all_by_type: Dict[str, int] = {}
        for result in self.detection_history:
            for data_type, count in result.by_type.items():
                all_by_type[data_type] = all_by_type.get(data_type, 0) + count
        
        avg_risk = (
            sum(r.risk_score for r in self.detection_history) / total_scans
            if total_scans > 0 else 0.0
        )
        
        return {
            "total_scans": total_scans,
            "total_findings": total_findings,
            "findings_by_type": all_by_type,
            "average_risk_score": avg_risk,
            "custom_patterns_count": len(self.custom_patterns)
        }
