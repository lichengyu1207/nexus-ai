"""
数据隐私模块
Data Privacy Module

实现数据脱敏、敏感实体识别、匿名化等功能
"""

import hashlib
import json
import logging
import random
import re
import string
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EntityType(Enum):
    PHONE = "phone"
    ID_CARD = "id_card"
    EMAIL = "email"
    NAME = "name"
    ADDRESS = "address"
    BANK_CARD = "bank_card"
    IP_ADDRESS = "ip_address"
    LICENSE_PLATE = "license_plate"
    PASSWORD = "password"
    CREDIT_CARD = "credit_card"


class MaskStrategy(Enum):
    REPLACE = "replace"
    PARTIAL = "partial"
    HASH = "hash"
    RANDOM = "random"
    REMOVE = "remove"


@dataclass
class SensitiveEntity:
    entity_id: str
    entity_type: EntityType
    original_value: str
    masked_value: str
    position: Tuple[int, int]
    confidence: float
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "original_value": self.original_value[:2] + "***" if len(self.original_value) > 2 else "***",
            "masked_value": self.masked_value,
            "position": self.position,
            "confidence": self.confidence,
            "context": self.context[:50] + "..." if len(self.context) > 50 else self.context,
        }


class SensitiveEntityRecognizer:
    """敏感实体识别器"""
    
    def __init__(self):
        self.patterns = {
            EntityType.PHONE: [
                r'1[3-9]\d{9}',
                r'\d{3,4}-\d{7,8}',
                r'\(\d{3,4}\)\s*\d{7,8}',
            ],
            EntityType.ID_CARD: [
                r'\d{17}[\dXx]',
                r'\d{15}',
            ],
            EntityType.EMAIL: [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            EntityType.BANK_CARD: [
                r'\d{16,19}',
            ],
            EntityType.IP_ADDRESS: [
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            ],
            EntityType.LICENSE_PLATE: [
                r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5,6}',
            ],
            EntityType.CREDIT_CARD: [
                r'(?:\d{4}[-\s]?){3}\d{4}',
            ],
        }
        
        self.name_keywords = [
            '先生', '女士', '小姐', '同志', '经理', '总监', '董事长',
            '教授', '博士', '医生', '老师', '工程师',
        ]
        
        self.address_keywords = [
            '省', '市', '区', '县', '镇', '乡', '村', '街道', '路', '号',
            '小区', '花园', '大厦', '广场', '公寓', '别墅',
        ]
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_scans": 0,
            "entities_found": 0,
            "by_type": defaultdict(int),
        }
    
    def recognize(self, text: str) -> List[SensitiveEntity]:
        self.stats["total_scans"] += 1
        entities = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    entity = SensitiveEntity(
                        entity_id=f"ent_{uuid.uuid4().hex[:8]}",
                        entity_type=entity_type,
                        original_value=match.group(),
                        masked_value="",
                        position=(match.start(), match.end()),
                        confidence=0.9,
                        context=text[max(0, match.start() - 20):match.end() + 20],
                    )
                    entities.append(entity)
                    
                    self.stats["entities_found"] += 1
                    self.stats["by_type"][entity_type.value] += 1
        
        entities.extend(self._recognize_names(text))
        entities.extend(self._recognize_addresses(text))
        
        return entities
    
    def _recognize_names(self, text: str) -> List[SensitiveEntity]:
        entities = []
        
        for keyword in self.name_keywords:
            pattern = rf'([\u4e00-\u9fa5]{{2,4}})\s*{keyword}'
            for match in re.finditer(pattern, text):
                entity = SensitiveEntity(
                    entity_id=f"ent_{uuid.uuid4().hex[:8]}",
                    entity_type=EntityType.NAME,
                    original_value=match.group(1),
                    masked_value="",
                    position=(match.start(1), match.end(1)),
                    confidence=0.7,
                    context=text[max(0, match.start() - 10):match.end() + 10],
                )
                entities.append(entity)
                
                self.stats["entities_found"] += 1
                self.stats["by_type"][EntityType.NAME.value] += 1
        
        return entities
    
    def _recognize_addresses(self, text: str) -> List[SensitiveEntity]:
        entities = []
        
        pattern = r'([\u4e00-\u9fa5]+(?:省|市|区|县)[\u4e00-\u9fa5]+(?:路|街|号|小区|花园|大厦))'
        
        for match in re.finditer(pattern, text):
            entity = SensitiveEntity(
                entity_id=f"ent_{uuid.uuid4().hex[:8]}",
                entity_type=EntityType.ADDRESS,
                original_value=match.group(),
                masked_value="",
                position=(match.start(), match.end()),
                confidence=0.8,
                context=text[max(0, match.start() - 10):match.end() + 10],
            )
            entities.append(entity)
            
            self.stats["entities_found"] += 1
            self.stats["by_type"][EntityType.ADDRESS.value] += 1
        
        return entities
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "by_type": dict(self.stats["by_type"]),
        }


class AnonymizationEngine:
    """匿名化引擎"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        
        self.fake_names = [
            "张三", "李四", "王五", "赵六", "钱七",
            "孙八", "周九", "吴十", "郑一", "王二",
        ]
        
        self.fake_addresses = [
            "北京市朝阳区***路***号",
            "上海市浦东新区***路***号",
            "广州市天河区***路***号",
            "深圳市南山区***路***号",
        ]
        
        self.mapping: Dict[str, str] = {}
        self._lock = threading.Lock()
        
        self.stats = {
            "total_anonymized": 0,
            "unique_mappings": 0,
        }
    
    def anonymize(
        self,
        entity: SensitiveEntity,
        strategy: MaskStrategy = MaskStrategy.PARTIAL
    ) -> str:
        self.stats["total_anonymized"] += 1
        
        key = f"{entity.entity_type.value}:{entity.original_value}"
        
        with self._lock:
            if key in self.mapping:
                return self.mapping[key]
        
        if strategy == MaskStrategy.REPLACE:
            masked = self._replace(entity)
        elif strategy == MaskStrategy.PARTIAL:
            masked = self._partial_mask(entity)
        elif strategy == MaskStrategy.HASH:
            masked = self._hash_mask(entity)
        elif strategy == MaskStrategy.RANDOM:
            masked = self._random_mask(entity)
        else:
            masked = self._partial_mask(entity)
        
        with self._lock:
            self.mapping[key] = masked
            self.stats["unique_mappings"] = len(self.mapping)
        
        return masked
    
    def _replace(self, entity: SensitiveEntity) -> str:
        if entity.entity_type == EntityType.NAME:
            return random.choice(self.fake_names)
        elif entity.entity_type == EntityType.ADDRESS:
            return random.choice(self.fake_addresses)
        elif entity.entity_type == EntityType.EMAIL:
            return "user***@example.com"
        else:
            return "[已脱敏]"
    
    def _partial_mask(self, entity: SensitiveEntity) -> str:
        value = entity.original_value
        length = len(value)
        
        if length <= 2:
            return "*" * length
        elif length <= 4:
            return value[0] + "*" * (length - 1)
        elif length <= 8:
            return value[:2] + "*" * (length - 4) + value[-2:]
        else:
            return value[:3] + "*" * (length - 6) + value[-3:]
    
    def _hash_mask(self, entity: SensitiveEntity) -> str:
        hash_value = hashlib.sha256(entity.original_value.encode()).hexdigest()[:8]
        return f"[HASH:{hash_value}]"
    
    def _random_mask(self, entity: SensitiveEntity) -> str:
        length = len(entity.original_value)
        
        if entity.entity_type == EntityType.PHONE:
            return f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}"
        elif entity.entity_type == EntityType.EMAIL:
            chars = string.ascii_lowercase + string.digits
            username = ''.join(random.choice(chars) for _ in range(8))
            return f"{username}@example.com"
        else:
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def get_mapping(self, masked_value: str) -> Optional[str]:
        with self._lock:
            for key, value in self.mapping.items():
                if value == masked_value:
                    return key.split(":", 1)[1]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
        }


class DataMasker:
    """数据脱敏器主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.recognizer = SensitiveEntityRecognizer()
        self.anonymizer = AnonymizationEngine(
            seed=self.config.get("seed", 42)
        )
        
        self.default_strategies: Dict[EntityType, MaskStrategy] = {
            EntityType.PHONE: MaskStrategy.PARTIAL,
            EntityType.ID_CARD: MaskStrategy.PARTIAL,
            EntityType.EMAIL: MaskStrategy.PARTIAL,
            EntityType.NAME: MaskStrategy.REPLACE,
            EntityType.ADDRESS: MaskStrategy.PARTIAL,
            EntityType.BANK_CARD: MaskStrategy.PARTIAL,
            EntityType.IP_ADDRESS: MaskStrategy.PARTIAL,
            EntityType.LICENSE_PLATE: MaskStrategy.PARTIAL,
            EntityType.PASSWORD: MaskStrategy.REMOVE,
            EntityType.CREDIT_CARD: MaskStrategy.PARTIAL,
        }
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_masked": 0,
            "total_entities_processed": 0,
        }
    
    def mask(
        self,
        text: str,
        strategy: MaskStrategy = None,
        entity_types: List[EntityType] = None
    ) -> Tuple[str, List[SensitiveEntity]]:
        self.stats["total_masked"] += 1
        
        entities = self.recognizer.recognize(text)
        
        if entity_types:
            entities = [e for e in entities if e.entity_type in entity_types]
        
        masked_text = text
        offset = 0
        
        sorted_entities = sorted(entities, key=lambda e: e.position[0])
        
        for entity in sorted_entities:
            start, end = entity.position
            adjusted_start = start + offset
            adjusted_end = end + offset
            
            entity_strategy = strategy or self.default_strategies.get(
                entity.entity_type, MaskStrategy.PARTIAL
            )
            
            masked_value = self.anonymizer.anonymize(entity, entity_strategy)
            entity.masked_value = masked_value
            
            masked_text = masked_text[:adjusted_start] + masked_value + masked_text[adjusted_end:]
            offset += len(masked_value) - (end - start)
            
            self.stats["total_entities_processed"] += 1
        
        return masked_text, entities
    
    def mask_dict(
        self,
        data: Dict[str, Any],
        fields_to_mask: List[str] = None
    ) -> Tuple[Dict[str, Any], List[SensitiveEntity]]:
        result = data.copy()
        all_entities = []
        
        fields = fields_to_mask or list(data.keys())
        
        for field in fields:
            if field in result and isinstance(result[field], str):
                masked_value, entities = self.mask(result[field])
                result[field] = masked_value
                all_entities.extend(entities)
        
        return result, all_entities
    
    def mask_list(
        self,
        items: List[str],
        strategy: MaskStrategy = None
    ) -> Tuple[List[str], List[List[SensitiveEntity]]]:
        masked_items = []
        all_entities = []
        
        for item in items:
            masked_item, entities = self.mask(item, strategy)
            masked_items.append(masked_item)
            all_entities.append(entities)
        
        return masked_items, all_entities
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "masker": self.stats,
            "recognizer": self.recognizer.get_stats(),
            "anonymizer": self.anonymizer.get_stats(),
        }


class ReversibleMasker:
    """可逆脱敏器"""
    
    def __init__(self, secret_key: str = "default_secret_key"):
        self.secret_key = secret_key
        self.mapping_store: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._lock = threading.Lock()
        
        self.stats = {
            "total_reversible_masks": 0,
            "total_reversals": 0,
        }
    
    def mask_with_key(
        self,
        value: str,
        entity_type: str,
        context: str = ""
    ) -> str:
        self.stats["total_reversible_masks"] += 1
        
        masked_id = hashlib.sha256(
            f"{self.secret_key}:{entity_type}:{value}:{context}".encode()
        ).hexdigest()[:16]
        
        token = f"[MASKED:{masked_id}]"
        
        with self._lock:
            self.mapping_store[entity_type][token] = value
        
        return token
    
    def unmask(self, token: str, entity_type: str = None) -> Optional[str]:
        self.stats["total_reversals"] += 1
        
        if not token.startswith("[MASKED:") or not token.endswith("]"):
            return None
        
        with self._lock:
            if entity_type:
                return self.mapping_store.get(entity_type, {}).get(token)
            else:
                for type_mappings in self.mapping_store.values():
                    if token in type_mappings:
                        return type_mappings[token]
        
        return None
    
    def export_mapping(self, password: str = None) -> Dict[str, Any]:
        with self._lock:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "mapping": dict(self.mapping_store),
            }
            
            if password:
                export_data["hash"] = hashlib.sha256(
                    (password + json.dumps(export_data["mapping"])).encode()
                ).hexdigest()
            
            return export_data
    
    def import_mapping(
        self,
        export_data: Dict[str, Any],
        password: str = None,
        merge: bool = True
    ) -> bool:
        if password and "hash" in export_data:
            expected_hash = hashlib.sha256(
                (password + json.dumps(export_data["mapping"])).encode()
            ).hexdigest()
            if export_data["hash"] != expected_hash:
                return False
        
        with self._lock:
            if merge:
                for entity_type, mappings in export_data.get("mapping", {}).items():
                    self.mapping_store[entity_type].update(mappings)
            else:
                self.mapping_store = defaultdict(dict, export_data.get("mapping", {}))
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "total_mappings": sum(len(m) for m in self.mapping_store.values()),
            "entity_types": list(self.mapping_store.keys()),
        }
