"""
样本隐私保护器
对样本库中的敏感数据进行脱敏和加密
"""
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AnonymizationMethod(str, Enum):
    HASH = "hash"
    MASK = "mask"
    GENERALIZE = "generalize"
    PERTURB = "perturb"
    SUPPRESS = "suppress"


class AccessPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class PIIDetector:
    PATTERNS = {
        "id_card_cn": {
            "pattern": r'\b\d{17}[\dXx]\b',
            "description": "Chinese ID Card Number",
            "sensitivity": "high"
        },
        "phone_cn": {
            "pattern": r'\b1[3-9]\d{9}\b',
            "description": "Chinese Phone Number",
            "sensitivity": "medium"
        },
        "email": {
            "pattern": r'\b[\w\.-]+@[\w\.-]+\.\w+\b',
            "description": "Email Address",
            "sensitivity": "medium"
        },
        "credit_card": {
            "pattern": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "description": "Credit Card Number",
            "sensitivity": "critical"
        },
        "passport": {
            "pattern": r'\b[A-Z]{1,2}\d{6,9}\b',
            "description": "Passport Number",
            "sensitivity": "high"
        },
        "bank_account": {
            "pattern": r'\b\d{16,19}\b',
            "description": "Bank Account Number",
            "sensitivity": "critical"
        },
        "name_cn": {
            "pattern": r'[\u4e00-\u9fa5]{2,4}',
            "description": "Chinese Name (potential)",
            "sensitivity": "low"
        },
        "address_cn": {
            "pattern": r'[\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+区',
            "description": "Chinese Address",
            "sensitivity": "medium"
        }
    }
    
    def __init__(self, custom_patterns: Optional[Dict[str, Dict[str, str]]] = None):
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
    
    def detect(self, text: str) -> List[Dict[str, Any]]:
        detections = []
        
        for pii_type, config in self.patterns.items():
            matches = re.findall(config["pattern"], text)
            if matches:
                detections.append({
                    "type": pii_type,
                    "description": config["description"],
                    "sensitivity": config["sensitivity"],
                    "count": len(matches),
                    "positions": [
                        m.start() for m in re.finditer(config["pattern"], text)
                    ]
                })
        
        return detections
    
    def get_sensitivity_score(self, detections: List[Dict[str, Any]]) -> float:
        if not detections:
            return 0.0
        
        sensitivity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.1
        }
        
        max_sensitivity = max(
            sensitivity_weights.get(d["sensitivity"], 0.5)
            for d in detections
        )
        
        return max_sensitivity


class Anonymizer:
    def __init__(self, salt: str = "fangdudu_privacy_salt"):
        self.salt = salt
    
    def anonymize(
        self,
        value: str,
        method: AnonymizationMethod,
        pii_type: Optional[str] = None
    ) -> str:
        if method == AnonymizationMethod.HASH:
            return self._hash_value(value)
        elif method == AnonymizationMethod.MASK:
            return self._mask_value(value, pii_type)
        elif method == AnonymizationMethod.GENERALIZE:
            return self._generalize_value(value, pii_type)
        elif method == AnonymizationMethod.PERTURB:
            return self._perturb_value(value, pii_type)
        elif method == AnonymizationMethod.SUPPRESS:
            return "[REDACTED]"
        
        return value
    
    def _hash_value(self, value: str) -> str:
        hashed = hashlib.sha256(f"{self.salt}{value}".encode()).hexdigest()
        return f"[HASH:{hashed[:16]}]"
    
    def _mask_value(self, value: str, pii_type: Optional[str]) -> str:
        if pii_type == "phone_cn":
            return value[:3] + "****" + value[-4:]
        elif pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
        elif pii_type == "id_card_cn":
            return value[:6] + "********" + value[-4:]
        elif pii_type == "credit_card" or pii_type == "bank_account":
            return "**** **** **** " + value[-4:]
        
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _generalize_value(self, value: str, pii_type: Optional[str]) -> str:
        if pii_type == "address_cn":
            match = re.match(r'([\u4e00-\u9fa5]+省)([\u4e00-\u9fa5]+市)', value)
            if match:
                return f"{match.group(1)}{match.group(2)}[某区]"
        elif pii_type == "phone_cn":
            return f"{value[:3]}****0000"
        
        return "[GENERALIZED]"
    
    def _perturb_value(self, value: str, pii_type: Optional[str]) -> str:
        import random
        
        if pii_type in ["phone_cn", "credit_card", "bank_account"]:
            digits = [d for d in value if d.isdigit()]
            if digits:
                perturbed = digits.copy()
                for i in range(len(perturbed) // 3):
                    idx = random.randint(0, len(perturbed) - 1)
                    perturbed[idx] = str(random.randint(0, 9))
                return "".join(perturbed)
        
        return value


class DifferentialPrivacy:
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon
    
    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        import random
        import math
        
        scale = sensitivity / self.epsilon
        noise = random.gauss(0, scale)
        
        return value + noise
    
    def add_noise_to_count(self, count: int) -> int:
        noisy = self.add_noise(float(count), sensitivity=1.0)
        return max(0, int(round(noisy)))
    
    def add_noise_to_sum(self, total: float, max_contribution: float) -> float:
        noisy = self.add_noise(total, sensitivity=max_contribution)
        return max(0.0, noisy)


class AccessControlManager:
    def __init__(self):
        self.agent_permissions: Dict[str, Set[str]] = {}
        self.sample_access_log: Dict[str, List[Dict[str, Any]]] = {}
        self.role_permissions: Dict[str, Set[str]] = {
            "admin": {"read", "write", "delete", "admin"},
            "analyst": {"read", "write"},
            "viewer": {"read"}
        }
        self.agent_roles: Dict[str, str] = {}
    
    def grant_permission(
        self,
        agent_id: str,
        permission: AccessPermission,
        sample_id: Optional[str] = None
    ):
        if agent_id not in self.agent_permissions:
            self.agent_permissions[agent_id] = set()
        
        key = f"{permission.value}:{sample_id}" if sample_id else permission.value
        self.agent_permissions[agent_id].add(key)
    
    def revoke_permission(
        self,
        agent_id: str,
        permission: AccessPermission,
        sample_id: Optional[str] = None
    ):
        if agent_id in self.agent_permissions:
            key = f"{permission.value}:{sample_id}" if sample_id else permission.value
            self.agent_permissions[agent_id].discard(key)
    
    def set_role(self, agent_id: str, role: str):
        self.agent_roles[agent_id] = role
    
    def check_permission(
        self,
        agent_id: str,
        permission: AccessPermission,
        sample_id: Optional[str] = None
    ) -> bool:
        role = self.agent_roles.get(agent_id)
        if role and role in self.role_permissions:
            if permission.value in self.role_permissions[role]:
                return True
        
        if agent_id in self.agent_permissions:
            specific_key = f"{permission.value}:{sample_id}"
            general_key = permission.value
            
            if specific_key in self.agent_permissions[agent_id]:
                return True
            if general_key in self.agent_permissions[agent_id]:
                return True
        
        return False
    
    def log_access(
        self,
        sample_id: str,
        agent_id: str,
        action: str,
        granted: bool
    ):
        if sample_id not in self.sample_access_log:
            self.sample_access_log[sample_id] = []
        
        self.sample_access_log[sample_id].append({
            "agent_id": agent_id,
            "action": action,
            "granted": granted,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_access_log(self, sample_id: str) -> List[Dict[str, Any]]:
        return self.sample_access_log.get(sample_id, [])


class SampleLifecycleManager:
    def __init__(
        self,
        default_retention_days: int = 365,
        max_retention_days: int = 1825
    ):
        self.default_retention_days = default_retention_days
        self.max_retention_days = max_retention_days
        
        self.sample_metadata: Dict[str, Dict[str, Any]] = {}
        self.deletion_requests: List[Dict[str, Any]] = []
    
    def register_sample(
        self,
        sample_id: str,
        privacy_level: PrivacyLevel,
        user_id: Optional[str] = None,
        retention_days: Optional[int] = None
    ):
        retention = min(
            retention_days or self.default_retention_days,
            self.max_retention_days
        )
        
        self.sample_metadata[sample_id] = {
            "privacy_level": privacy_level,
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=retention),
            "retention_days": retention
        }
    
    def request_deletion(
        self,
        sample_id: str,
        requester: str,
        reason: str
    ) -> bool:
        if sample_id not in self.sample_metadata:
            return False
        
        self.deletion_requests.append({
            "sample_id": sample_id,
            "requester": requester,
            "reason": reason,
            "requested_at": datetime.now().isoformat(),
            "status": "pending"
        })
        
        return True
    
    def process_deletion_request(self, request_id: str, approved: bool) -> bool:
        for request in self.deletion_requests:
            if request.get("request_id") == request_id:
                request["status"] = "approved" if approved else "rejected"
                request["processed_at"] = datetime.now().isoformat()
                return True
        return False
    
    def get_expired_samples(self) -> List[str]:
        now = datetime.now()
        return [
            sample_id for sample_id, meta in self.sample_metadata.items()
            if meta["expires_at"] < now
        ]
    
    def extend_retention(self, sample_id: str, additional_days: int) -> bool:
        if sample_id not in self.sample_metadata:
            return False
        
        meta = self.sample_metadata[sample_id]
        new_expiry = meta["expires_at"] + timedelta(days=additional_days)
        
        max_expiry = meta["created_at"] + timedelta(days=self.max_retention_days)
        if new_expiry > max_expiry:
            new_expiry = max_expiry
        
        meta["expires_at"] = new_expiry
        return True


class SamplePrivacyProtector:
    def __init__(
        self,
        sample_repository: Optional[Any] = None,
        default_epsilon: float = 1.0
    ):
        self.sample_repository = sample_repository
        
        self.pii_detector = PIIDetector()
        self.anonymizer = Anonymizer()
        self.differential_privacy = DifferentialPrivacy(epsilon=default_epsilon)
        self.access_control = AccessControlManager()
        self.lifecycle_manager = SampleLifecycleManager()
        
        self.anonymization_rules: Dict[str, AnonymizationMethod] = {
            "id_card_cn": AnonymizationMethod.MASK,
            "phone_cn": AnonymizationMethod.MASK,
            "email": AnonymizationMethod.MASK,
            "credit_card": AnonymizationMethod.HASH,
            "passport": AnonymizationMethod.HASH,
            "bank_account": AnonymizationMethod.HASH,
            "name_cn": AnonymizationMethod.HASH,
            "address_cn": AnonymizationMethod.GENERALIZE
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def protect_sample(
        self,
        sample: Dict[str, Any],
        privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    ) -> Dict[str, Any]:
        content = sample.get("content", {})
        
        if isinstance(content, str):
            content = {"text": content}
        
        content_str = json.dumps(content, ensure_ascii=False)
        detections = self.pii_detector.detect(content_str)
        
        if detections:
            anonymized_content = await self._anonymize_content(content, detections)
            sample["content"] = anonymized_content
            sample["pii_detected"] = [d["type"] for d in detections]
            sample["sensitivity_score"] = self.pii_detector.get_sensitivity_score(detections)
        
        sample["privacy_level"] = privacy_level.value
        sample["protected_at"] = datetime.now().isoformat()
        
        self.lifecycle_manager.register_sample(
            sample.get("id", str(uuid4())),
            privacy_level
        )
        
        return sample
    
    async def _anonymize_content(
        self,
        content: Dict[str, Any],
        detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        content_str = json.dumps(content, ensure_ascii=False)
        
        for detection in detections:
            pii_type = detection["type"]
            method = self.anonymization_rules.get(pii_type, AnonymizationMethod.HASH)
            
            pattern_config = self.pii_detector.patterns.get(pii_type, {})
            pattern = pattern_config.get("pattern", "")
            
            if pattern:
                def replace_match(match):
                    return self.anonymizer.anonymize(match.group(), method, pii_type)
                
                content_str = re.sub(pattern, replace_match, content_str)
        
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            return {"text": content_str}
    
    async def check_access(
        self,
        agent_id: str,
        sample_id: str,
        action: str
    ) -> bool:
        permission_map = {
            "read": AccessPermission.READ,
            "write": AccessPermission.WRITE,
            "delete": AccessPermission.DELETE
        }
        
        permission = permission_map.get(action, AccessPermission.READ)
        
        granted = self.access_control.check_permission(
            agent_id,
            permission,
            sample_id
        )
        
        self.access_control.log_access(sample_id, agent_id, action, granted)
        
        if not granted:
            self.logger.warning(
                f"Access denied: agent={agent_id}, sample={sample_id}, action={action}"
            )
        
        return granted
    
    def grant_access(
        self,
        agent_id: str,
        permission: AccessPermission,
        sample_id: Optional[str] = None
    ):
        self.access_control.grant_permission(agent_id, permission, sample_id)
        self.logger.info(f"Granted {permission.value} access to {agent_id} for {sample_id or 'all'}")
    
    def set_agent_role(self, agent_id: str, role: str):
        self.access_control.set_role(agent_id, role)
    
    async def apply_differential_privacy(
        self,
        data: Dict[str, Any],
        epsilon: Optional[float] = None
    ) -> Dict[str, Any]:
        if epsilon:
            self.differential_privacy.epsilon = epsilon
        
        protected = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                protected[key] = self.differential_privacy.add_noise(float(value))
            elif isinstance(value, dict):
                protected[key] = await self.apply_differential_privacy(value, epsilon)
            else:
                protected[key] = value
        
        return protected
    
    async def handle_deletion_request(
        self,
        user_id: str,
        sample_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if sample_ids:
            samples_to_delete = sample_ids
        else:
            samples_to_delete = [
                sid for sid, meta in self.lifecycle_manager.sample_metadata.items()
                if meta.get("user_id") == user_id
            ]
        
        deleted = []
        for sample_id in samples_to_delete:
            if self.sample_repository:
                success = await self.sample_repository.delete(sample_id)
                if success:
                    deleted.append(sample_id)
                    if sample_id in self.lifecycle_manager.sample_metadata:
                        del self.lifecycle_manager.sample_metadata[sample_id]
        
        return {
            "user_id": user_id,
            "requested_count": len(samples_to_delete),
            "deleted_count": len(deleted),
            "deleted_samples": deleted
        }
    
    async def cleanup_expired_samples(self) -> int:
        expired = self.lifecycle_manager.get_expired_samples()
        
        deleted_count = 0
        for sample_id in expired:
            if self.sample_repository:
                success = await self.sample_repository.delete(sample_id)
                if success:
                    deleted_count += 1
                    if sample_id in self.lifecycle_manager.sample_metadata:
                        del self.lifecycle_manager.sample_metadata[sample_id]
        
        self.logger.info(f"Cleaned up {deleted_count} expired samples")
        return deleted_count
    
    def get_audit_trail(self, sample_id: str) -> List[Dict[str, Any]]:
        return self.access_control.get_access_log(sample_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "registered_samples": len(self.lifecycle_manager.sample_metadata),
            "pending_deletions": len([
                r for r in self.lifecycle_manager.deletion_requests
                if r["status"] == "pending"
            ]),
            "agents_with_access": len(self.access_control.agent_permissions),
            "pii_types_detected": list(self.anonymization_rules.keys())
        }
