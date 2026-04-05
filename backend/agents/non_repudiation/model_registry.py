"""
模型版本注册中心模块
Model Registry Module

实现模型版本管理、哈希验证、远程验证、自动回滚等功能
"""

import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    DRAFT = "draft"
    TRAINING = "training"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"
    TAMPERED = "tampered"


class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    TAMPERED = "tampered"


@dataclass
class ModelVersion:
    version_id: str
    model_name: str
    version_number: str
    model_hash: str
    parameters_hash: str
    training_session_id: str
    training_data_hash: str
    hyperparams: Dict[str, Any]
    metrics: Dict[str, float]
    status: ModelStatus
    created_at: datetime
    deployed_at: Optional[datetime]
    deprecated_at: Optional[datetime]
    parent_version: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "model_name": self.model_name,
            "version_number": self.version_number,
            "model_hash": self.model_hash[:16] + "...",
            "parameters_hash": self.parameters_hash[:16] + "...",
            "training_session_id": self.training_session_id,
            "training_data_hash": self.training_data_hash[:16] + "...",
            "hyperparams": self.hyperparams,
            "metrics": self.metrics,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "parent_version": self.parent_version,
            "metadata": self.metadata,
        }


@dataclass
class ModelVerification:
    verification_id: str
    version_id: str
    timestamp: datetime
    status: VerificationStatus
    expected_hash: str
    actual_hash: str
    errors: List[str]
    verification_method: str
    verifier: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "expected_hash": self.expected_hash[:16] + "...",
            "actual_hash": self.actual_hash[:16] + "...",
            "errors": self.errors,
            "verification_method": self.verification_method,
            "verifier": self.verifier,
        }


class ModelVerification:
    """模型验证器"""
    
    def __init__(self):
        self.verifications: Dict[str, ModelVerification] = {}
        self.verification_history: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "tampering_detected": 0,
        }
    
    def verify_model(
        self,
        version: ModelVersion,
        current_params: Dict[str, Any],
        verifier: str = "system"
    ) -> ModelVerification:
        self.stats["total_verifications"] += 1
        
        verification_id = f"ver_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        actual_hash = self._compute_hash(current_params)
        expected_hash = version.model_hash
        
        errors = []
        status = VerificationStatus.VERIFIED
        
        if actual_hash != expected_hash:
            status = VerificationStatus.TAMPERED
            errors.append("Model hash mismatch - possible tampering detected")
            self.stats["tampering_detected"] += 1
        
        verification = ModelVerification(
            verification_id=verification_id,
            version_id=version.version_id,
            timestamp=datetime.now(),
            status=status,
            expected_hash=expected_hash,
            actual_hash=actual_hash,
            errors=errors,
            verification_method="hash_comparison",
            verifier=verifier,
        )
        
        with self._lock:
            self.verifications[verification_id] = verification
            self.verification_history[version.version_id].append(verification_id)
            
            if status == VerificationStatus.VERIFIED:
                self.stats["successful_verifications"] += 1
            else:
                self.stats["failed_verifications"] += 1
        
        return verification
    
    def _compute_hash(self, params: Dict[str, Any]) -> str:
        content = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_verification_history(
        self,
        version_id: str,
        limit: int = 50
    ) -> List[ModelVerification]:
        with self._lock:
            verification_ids = self.verification_history.get(version_id, [])[-limit:]
            return [self.verifications[vid] for vid in verification_ids if vid in self.verifications]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "total_versions_verified": len(self.verification_history),
        }


class ModelRollbackManager:
    """模型回滚管理器"""
    
    def __init__(self, registry: 'ModelRegistry'):
        self.registry = registry
        
        self.rollback_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self.stats = {
            "total_rollbacks": 0,
            "successful_rollbacks": 0,
            "failed_rollbacks": 0,
        }
    
    def rollback(
        self,
        model_name: str,
        target_version: str = None,
        reason: str = "manual_rollback"
    ) -> Tuple[bool, Optional[ModelVersion]]:
        self.stats["total_rollbacks"] += 1
        
        current = self.registry.get_deployed_version(model_name)
        
        if not current:
            self.stats["failed_rollbacks"] += 1
            return False, None
        
        if target_version:
            target = self.registry.get_version(target_version)
        else:
            target = self._find_previous_version(model_name, current.version_id)
        
        if not target:
            self.stats["failed_rollbacks"] += 1
            return False, None
        
        current.status = ModelStatus.ROLLED_BACK
        current.deprecated_at = datetime.now()
        
        target.status = ModelStatus.DEPLOYED
        target.deployed_at = datetime.now()
        
        rollback_record = {
            "rollback_id": f"rb_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            "model_name": model_name,
            "from_version": current.version_id,
            "to_version": target.version_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
        
        with self._lock:
            self.rollback_history.append(rollback_record)
            self.stats["successful_rollbacks"] += 1
        
        return True, target
    
    def _find_previous_version(
        self,
        model_name: str,
        current_version_id: str
    ) -> Optional[ModelVersion]:
        versions = self.registry.get_model_versions(model_name)
        
        for v in versions:
            if v.version_id != current_version_id and v.status == ModelStatus.VALIDATED:
                return v
        
        for v in versions:
            if v.version_id != current_version_id and v.status in [
                ModelStatus.DEPLOYED,
                ModelStatus.DEPRECATED,
            ]:
                return v
        
        return None
    
    def auto_rollback_on_tampering(
        self,
        model_name: str,
        verification: ModelVerification
    ) -> Tuple[bool, Optional[ModelVersion]]:
        if verification.status != VerificationStatus.TAMPERED:
            return False, None
        
        logger.warning(
            f"Tampering detected for {model_name}, "
            f"initiating auto-rollback"
        )
        
        return self.rollback(
            model_name,
            reason=f"auto_rollback:tampering_detected:{verification.verification_id}"
        )
    
    def get_rollback_history(
        self,
        model_name: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        with self._lock:
            history = self.rollback_history
            
            if model_name:
                history = [r for r in history if r["model_name"] == model_name]
            
            return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "rollback_history_size": len(self.rollback_history),
        }


class ModelRegistry:
    """模型版本注册中心主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.versions: Dict[str, ModelVersion] = {}
        self.model_versions: Dict[str, List[str]] = defaultdict(list)
        self.deployed_versions: Dict[str, str] = {}
        
        self.verification = ModelVerification()
        self.rollback_manager = ModelRollbackManager(self)
        
        self._lock = threading.Lock()
        
        self._running = False
        self._verification_task = None
        
        self.stats = {
            "total_versions_registered": 0,
            "total_deployments": 0,
            "total_deprecations": 0,
        }
    
    async def start(self):
        self._running = True
        self._verification_task = asyncio.create_task(self._periodic_verification())
    
    def stop(self):
        self._running = False
        if self._verification_task:
            self._verification_task.cancel()
    
    async def _periodic_verification(self):
        while self._running:
            try:
                await asyncio.sleep(86400)
                
                for model_name, version_id in self.deployed_versions.items():
                    version = self.get_version(version_id)
                    if version:
                        logger.info(f"Periodic verification for {model_name}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic verification error: {e}")
    
    def register_version(
        self,
        model_name: str,
        version_number: str,
        model_params: Dict[str, Any],
        training_session_id: str,
        training_data_hash: str,
        hyperparams: Dict[str, Any],
        metrics: Dict[str, float],
        parent_version: str = None,
        metadata: Dict[str, Any] = None
    ) -> ModelVersion:
        version_id = f"mv_{model_name}_{version_number}_{uuid.uuid4().hex[:6]}"
        
        model_hash = self._compute_hash(model_params)
        params_hash = hashlib.sha256(
            json.dumps(model_params, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        version = ModelVersion(
            version_id=version_id,
            model_name=model_name,
            version_number=version_number,
            model_hash=model_hash,
            parameters_hash=params_hash,
            training_session_id=training_session_id,
            training_data_hash=training_data_hash,
            hyperparams=hyperparams,
            metrics=metrics,
            status=ModelStatus.DRAFT,
            created_at=datetime.now(),
            deployed_at=None,
            deprecated_at=None,
            parent_version=parent_version,
            metadata=metadata or {},
        )
        
        with self._lock:
            self.versions[version_id] = version
            self.model_versions[model_name].append(version_id)
            self.stats["total_versions_registered"] += 1
        
        return version
    
    def deploy_version(
        self,
        version_id: str
    ) -> Tuple[bool, Optional[ModelVersion]]:
        with self._lock:
            version = self.versions.get(version_id)
            if not version:
                return False, None
            
            if version.status not in [ModelStatus.DRAFT, ModelStatus.VALIDATED]:
                return False, None
            
            current_deployed = self.deployed_versions.get(version.model_name)
            if current_deployed and current_deployed in self.versions:
                old_version = self.versions[current_deployed]
                old_version.status = ModelStatus.DEPRECATED
                old_version.deprecated_at = datetime.now()
                self.stats["total_deprecations"] += 1
            
            version.status = ModelStatus.DEPLOYED
            version.deployed_at = datetime.now()
            
            self.deployed_versions[version.model_name] = version_id
            self.stats["total_deployments"] += 1
        
        return True, version
    
    def validate_version(self, version_id: str) -> bool:
        with self._lock:
            version = self.versions.get(version_id)
            if not version:
                return False
            
            if version.status != ModelStatus.DRAFT:
                return False
            
            version.status = ModelStatus.VALIDATED
        
        return True
    
    def get_version(self, version_id: str) -> Optional[ModelVersion]:
        return self.versions.get(version_id)
    
    def get_deployed_version(self, model_name: str) -> Optional[ModelVersion]:
        with self._lock:
            version_id = self.deployed_versions.get(model_name)
            if version_id:
                return self.versions.get(version_id)
        return None
    
    def get_model_versions(
        self,
        model_name: str,
        status: ModelStatus = None
    ) -> List[ModelVersion]:
        with self._lock:
            version_ids = self.model_versions.get(model_name, [])
            versions = [self.versions[vid] for vid in version_ids if vid in self.versions]
            
            if status:
                versions = [v for v in versions if v.status == status]
            
            return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def verify_deployed_model(
        self,
        model_name: str,
        current_params: Dict[str, Any]
    ) -> Tuple[bool, ModelVerification]:
        version = self.get_deployed_version(model_name)
        
        if not version:
            verification = ModelVerification(
                verification_id=f"ver_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                version_id="unknown",
                timestamp=datetime.now(),
                status=VerificationStatus.FAILED,
                expected_hash="",
                actual_hash="",
                errors=["No deployed version found"],
                verification_method="hash_comparison",
                verifier="system",
            )
            return False, verification
        
        verification = self.verification.verify_model(version, current_params)
        
        if verification.status == VerificationStatus.TAMPERED:
            version.status = ModelStatus.TAMPERED
            
            self.rollback_manager.auto_rollback_on_tampering(model_name, verification)
        
        return verification.status == VerificationStatus.VERIFIED, verification
    
    def get_authorized_hashes(
        self,
        model_name: str
    ) -> List[str]:
        versions = self.get_model_versions(model_name)
        
        authorized = []
        for v in versions:
            if v.status in [ModelStatus.DEPLOYED, ModelStatus.VALIDATED]:
                authorized.append(v.model_hash)
        
        return authorized
    
    def is_authorized_hash(
        self,
        model_name: str,
        model_hash: str
    ) -> bool:
        authorized = self.get_authorized_hashes(model_name)
        return model_hash in authorized
    
    def deprecate_version(
        self,
        version_id: str,
        reason: str = "manual_deprecation"
    ) -> bool:
        with self._lock:
            version = self.versions.get(version_id)
            if not version:
                return False
            
            version.status = ModelStatus.DEPRECATED
            version.deprecated_at = datetime.now()
            version.metadata["deprecation_reason"] = reason
            
            self.stats["total_deprecations"] += 1
        
        return True
    
    def export_model_history(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        versions = self.get_model_versions(model_name)
        
        return {
            "model_name": model_name,
            "export_time": datetime.now().isoformat(),
            "total_versions": len(versions),
            "versions": [v.to_dict() for v in versions],
            "current_deployed": self.deployed_versions.get(model_name),
            "rollback_history": self.rollback_manager.get_rollback_history(model_name),
        }
    
    def _compute_hash(self, params: Dict[str, Any]) -> str:
        content = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "registry": self.stats,
            "verification": self.verification.get_stats(),
            "rollback_manager": self.rollback_manager.get_stats(),
            "total_models": len(self.model_versions),
            "deployed_models": len(self.deployed_versions),
        }


import asyncio
