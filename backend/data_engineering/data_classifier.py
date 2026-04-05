"""
数据分类分级 - 敏感数据识别
自动扫描数据库识别敏感字段，应用不同加密策略
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Pattern
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging
import asyncio
import asyncpg
import json

logger = logging.getLogger(__name__)


class DataSensitivity(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class DataType(Enum):
    PERSONAL_ID = "personal_id"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"
    PASSWORD = "password"
    IP_ADDRESS = "ip_address"
    MEDICAL_RECORD = "medical_record"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC = "biometric"
    LOCATION = "location"
    BIRTH_DATE = "birth_date"
    GENERAL = "general"


class EncryptionMethod(Enum):
    NONE = "none"
    HASH = "hash"
    AES128 = "aes128"
    AES256 = "aes256"
    RSA = "rsa"
    MASKING = "masking"


@dataclass
class SensitiveField:
    table_name: str
    column_name: str
    data_type: DataType
    sensitivity: DataSensitivity
    encryption_method: EncryptionMethod
    pattern_matched: str
    sample_count: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationRule:
    rule_id: str
    data_type: DataType
    sensitivity: DataSensitivity
    patterns: List[str]
    column_name_patterns: List[str]
    encryption_method: EncryptionMethod
    description: str


SENSITIVE_PATTERNS: Dict[DataType, List[str]] = {
    DataType.PERSONAL_ID: [
        r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$',
        r'^[A-Z]{1,2}\d{6}[A-D0-9]$',
    ],
    DataType.PHONE_NUMBER: [
        r'^1[3-9]\d{9}$',
        r'^\+?86[-\s]?1[3-9]\d{9}$',
        r'^\d{3,4}[-\s]?\d{7,8}$',
    ],
    DataType.EMAIL: [
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    ],
    DataType.BANK_ACCOUNT: [
        r'^\d{16,19}$',
        r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{0,3}$',
    ],
    DataType.CREDIT_CARD: [
        r'^4\d{12}(\d{3})?$',
        r'^5[1-5]\d{14}$',
        r'^3[47]\d{13}$',
        r'^6(?:011|5\d{2})\d{12}$',
    ],
    DataType.IP_ADDRESS: [
        r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$',
        r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$',
    ],
}

COLUMN_NAME_PATTERNS: Dict[DataType, List[str]] = {
    DataType.PERSONAL_ID: [
        r'.*id_card.*', r'.*identity.*', r'.*sfz.*', r'.*sfzh.*',
        r'.*身份证.*', r'.*证件号.*'
    ],
    DataType.PHONE_NUMBER: [
        r'.*phone.*', r'.*mobile.*', r'.*tel.*', r'.*cell.*',
        r'.*电话.*', r'.*手机.*'
    ],
    DataType.EMAIL: [
        r'.*email.*', r'.*mail.*', r'.*邮箱.*'
    ],
    DataType.BANK_ACCOUNT: [
        r'.*bank.*', r'.*account.*', r'.*银行卡.*', r'.*账号.*'
    ],
    DataType.PASSWORD: [
        r'.*password.*', r'.*passwd.*', r'.*pwd.*', r'.*密码.*'
    ],
    DataType.ADDRESS: [
        r'.*address.*', r'.*addr.*', r'.*地址.*', r'.*location.*'
    ],
    DataType.NAME: [
        r'.*name.*', r'.*姓名.*', r'.*real_name.*', r'.*user_name.*'
    ],
    DataType.BIRTH_DATE: [
        r'.*birth.*', r'.*birthday.*', r'.*出生.*', r'.*dob.*'
    ],
}

SENSITIVITY_MAPPING: Dict[DataType, DataSensitivity] = {
    DataType.PERSONAL_ID: DataSensitivity.SECRET,
    DataType.PHONE_NUMBER: DataSensitivity.CONFIDENTIAL,
    DataType.EMAIL: DataSensitivity.CONFIDENTIAL,
    DataType.BANK_ACCOUNT: DataSensitivity.SECRET,
    DataType.CREDIT_CARD: DataSensitivity.TOP_SECRET,
    DataType.PASSWORD: DataSensitivity.TOP_SECRET,
    DataType.IP_ADDRESS: DataSensitivity.INTERNAL,
    DataType.ADDRESS: DataSensitivity.CONFIDENTIAL,
    DataType.NAME: DataSensitivity.CONFIDENTIAL,
    DataType.BIRTH_DATE: DataSensitivity.CONFIDENTIAL,
    DataType.MEDICAL_RECORD: DataSensitivity.TOP_SECRET,
    DataType.FINANCIAL_DATA: DataSensitivity.SECRET,
    DataType.BIOMETRIC: DataSensitivity.TOP_SECRET,
    DataType.LOCATION: DataSensitivity.CONFIDENTIAL,
    DataType.GENERAL: DataSensitivity.PUBLIC,
}

ENCRYPTION_MAPPING: Dict[DataSensitivity, EncryptionMethod] = {
    DataSensitivity.PUBLIC: EncryptionMethod.NONE,
    DataSensitivity.INTERNAL: EncryptionMethod.AES128,
    DataSensitivity.CONFIDENTIAL: EncryptionMethod.AES256,
    DataSensitivity.SECRET: EncryptionMethod.AES256,
    DataSensitivity.TOP_SECRET: EncryptionMethod.AES256,
}


class DataClassifier:
    def __init__(self):
        self._compiled_patterns: Dict[DataType, List[Pattern]] = {}
        self._compiled_column_patterns: Dict[DataType, List[Pattern]] = {}
        self._classification_rules: List[ClassificationRule] = []
        self._detected_fields: List[SensitiveField] = []
        
        self._compile_patterns()
        self._init_default_rules()
        
    def _compile_patterns(self):
        for data_type, patterns in SENSITIVE_PATTERNS.items():
            self._compiled_patterns[data_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
            
        for data_type, patterns in COLUMN_NAME_PATTERNS.items():
            self._compiled_column_patterns[data_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
            
    def _init_default_rules(self):
        for data_type in DataType:
            sensitivity = SENSITIVITY_MAPPING.get(data_type, DataSensitivity.INTERNAL)
            encryption = ENCRYPTION_MAPPING.get(sensitivity, EncryptionMethod.AES128)
            
            rule = ClassificationRule(
                rule_id=f"rule_{data_type.value}",
                data_type=data_type,
                sensitivity=sensitivity,
                patterns=SENSITIVE_PATTERNS.get(data_type, []),
                column_name_patterns=COLUMN_NAME_PATTERNS.get(data_type, []),
                encryption_method=encryption,
                description=f"Default rule for {data_type.value}"
            )
            self._classification_rules.append(rule)
            
    def add_custom_rule(self, rule: ClassificationRule):
        self._classification_rules.append(rule)
        
    def classify_value(self, value: str) -> Tuple[Optional[DataType], float]:
        if not value or not isinstance(value, str):
            return None, 0.0
            
        best_match = None
        best_confidence = 0.0
        
        for data_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(value.strip()):
                    confidence = 0.9
                    if confidence > best_confidence:
                        best_match = data_type
                        best_confidence = confidence
                        
        return best_match, best_confidence
        
    def classify_column_name(self, column_name: str) -> List[Tuple[DataType, float]]:
        matches = []
        
        for data_type, patterns in self._compiled_column_patterns.items():
            for pattern in patterns:
                if pattern.match(column_name.lower()):
                    matches.append((data_type, 0.7))
                    break
                    
        return matches
        
    def scan_table(
        self,
        table_name: str,
        columns: List[str],
        sample_data: Dict[str, List[str]]
    ) -> List[SensitiveField]:
        detected = []
        
        for column_name in columns:
            column_matches = self.classify_column_name(column_name)
            
            samples = sample_data.get(column_name, [])
            value_matches: Dict[DataType, int] = {}
            
            for sample in samples[:100]:
                if sample:
                    data_type, confidence = self.classify_value(str(sample))
                    if data_type and confidence > 0.5:
                        value_matches[data_type] = value_matches.get(data_type, 0) + 1
                        
            final_type = None
            final_confidence = 0.0
            
            if value_matches:
                best_value_match = max(value_matches.items(), key=lambda x: x[1])
                final_type = best_value_match[0]
                final_confidence = best_value_match[1] / len(samples) if samples else 0
                
            if column_matches and not final_type:
                final_type = column_matches[0][0]
                final_confidence = column_matches[0][1]
                
            if final_type:
                sensitivity = SENSITIVITY_MAPPING.get(final_type, DataSensitivity.INTERNAL)
                encryption = ENCRYPTION_MAPPING.get(sensitivity, EncryptionMethod.AES128)
                
                field = SensitiveField(
                    table_name=table_name,
                    column_name=column_name,
                    data_type=final_type,
                    sensitivity=sensitivity,
                    encryption_method=encryption,
                    pattern_matched=final_type.value,
                    sample_count=len(samples),
                    confidence=final_confidence
                )
                detected.append(field)
                
        self._detected_fields.extend(detected)
        return detected


class DatabaseScanner:
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        self.classifier = DataClassifier()
        
    async def scan_all_tables(self) -> List[SensitiveField]:
        all_detected = []
        
        async with self.pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            for table_row in tables:
                table_name = table_row["table_name"]
                
                columns = await conn.fetch("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                """, table_name)
                
                column_names = [c["column_name"] for c in columns]
                sample_data = {}
                
                for col in column_names:
                    try:
                        samples = await conn.fetch(f"""
                            SELECT DISTINCT {col} 
                            FROM {table_name} 
                            WHERE {col} IS NOT NULL 
                            LIMIT 100
                        """)
                        sample_data[col] = [str(s[col]) for s in samples if s[col]]
                    except Exception as e:
                        logger.warning(f"Error sampling {table_name}.{col}: {e}")
                        sample_data[col] = []
                        
                detected = self.classifier.scan_table(table_name, column_names, sample_data)
                all_detected.extend(detected)
                
        return all_detected
        
    async def get_classification_report(self) -> Dict[str, Any]:
        detected = await self.scan_all_tables()
        
        by_sensitivity: Dict[str, List[str]] = {
            s.value: [] for s in DataSensitivity
        }
        by_type: Dict[str, List[str]] = {
            t.value: [] for t in DataType
        }
        
        for field in detected:
            key = f"{field.table_name}.{field.column_name}"
            by_sensitivity[field.sensitivity.value].append(key)
            by_type[field.data_type.value].append(key)
            
        return {
            "scan_time": datetime.now().isoformat(),
            "total_sensitive_fields": len(detected),
            "by_sensitivity": {
                k: {"count": len(v), "fields": v}
                for k, v in by_sensitivity.items() if v
            },
            "by_type": {
                k: {"count": len(v), "fields": v}
                for k, v in by_type.items() if v
            },
            "recommendations": self._generate_recommendations(detected)
        }
        
    def _generate_recommendations(self, fields: List[SensitiveField]) -> List[str]:
        recommendations = []
        
        top_secret = [f for f in fields if f.sensitivity == DataSensitivity.TOP_SECRET]
        if top_secret:
            recommendations.append(
                f"发现 {len(top_secret)} 个最高敏感度字段，建议立即启用AES256加密"
            )
            
        unencrypted = [
            f for f in fields 
            if f.encryption_method == EncryptionMethod.NONE and 
            f.sensitivity != DataSensitivity.PUBLIC
        ]
        if unencrypted:
            recommendations.append(
                f"发现 {len(unencrypted)} 个敏感字段未加密，建议配置加密策略"
            )
            
        return recommendations


class DataMasker:
    MASKING_RULES = {
        DataType.PERSONAL_ID: lambda x: x[:6] + "********" + x[-4:] if len(x) >= 14 else x[:2] + "*" * (len(x) - 4) + x[-2:],
        DataType.PHONE_NUMBER: lambda x: x[:3] + "****" + x[-4:] if len(x) >= 7 else "*" * len(x),
        DataType.EMAIL: lambda x: x[0] + "***" + x[x.index("@"):] if "@" in x else "***",
        DataType.BANK_ACCOUNT: lambda x: x[:4] + "****" + x[-4:] if len(x) >= 8 else "*" * len(x),
        DataType.CREDIT_CARD: lambda x: x[:4] + " **** **** " + x[-4:] if len(x) >= 8 else "*" * len(x),
        DataType.NAME: lambda x: x[0] + "*" * (len(x) - 1) if len(x) > 1 else "*",
        DataType.ADDRESS: lambda x: x[:10] + "..." if len(x) > 10 else "*" * len(x),
    }
    
    def mask(self, value: str, data_type: DataType) -> str:
        if not value:
            return value
            
        masking_func = self.MASKING_RULES.get(data_type)
        if masking_func:
            try:
                return masking_func(value)
            except Exception:
                return "*" * len(value)
                
        return value


class DynamicDesensitizer:
    def __init__(self, scanner: DatabaseScanner):
        self.scanner = scanner
        self.masker = DataMasker()
        self._field_mappings: Dict[str, DataType] = {}
        
    async def initialize(self):
        fields = await self.scanner.scan_all_tables()
        for field in fields:
            key = f"{field.table_name}.{field.column_name}"
            self._field_mappings[key] = field.data_type
            
    def desensitize_record(
        self,
        table_name: str,
        record: Dict[str, Any],
        user_permission_level: str = "internal"
    ) -> Dict[str, Any]:
        permission_sensitivity = {
            "public": [DataSensitivity.PUBLIC],
            "internal": [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL],
            "confidential": [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL, DataSensitivity.CONFIDENTIAL],
            "secret": [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL, DataSensitivity.CONFIDENTIAL, DataSensitivity.SECRET],
            "top_secret": list(DataSensitivity),
        }
        
        allowed_sensitivities = permission_sensitivity.get(user_permission_level, [DataSensitivity.PUBLIC])
        
        desensitized = {}
        for key, value in record.items():
            field_key = f"{table_name}.{key}"
            data_type = self._field_mappings.get(field_key)
            
            if data_type:
                sensitivity = SENSITIVITY_MAPPING.get(data_type, DataSensitivity.INTERNAL)
                
                if sensitivity not in allowed_sensitivities:
                    desensitized[key] = self.masker.mask(str(value), data_type)
                else:
                    desensitized[key] = value
            else:
                desensitized[key] = value
                
        return desensitized


async def create_data_classifier(pool: asyncpg.Pool) -> Tuple[DatabaseScanner, DynamicDesensitizer]:
    scanner = DatabaseScanner(pool)
    desensitizer = DynamicDesensitizer(scanner)
    await desensitizer.initialize()
    return scanner, desensitizer
