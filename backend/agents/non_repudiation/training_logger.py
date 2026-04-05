"""
训练日志记录器模块
Training Logger Module

实现训练过程日志记录、签名验证、完整性检查等功能
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


class TrainingPhase(Enum):
    INIT = "init"
    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class LogStatus(Enum):
    PENDING = "pending"
    SIGNED = "signed"
    VERIFIED = "verified"
    TAMPERED = "tampered"


@dataclass
class TrainingRecord:
    record_id: str
    session_id: str
    epoch: int
    timestamp: datetime
    train_loss: float
    val_loss: float
    accuracy: float
    learning_rate: float
    model_hash: str
    prev_hash: str
    current_hash: str
    signature: str
    status: LogStatus
    metrics: Dict[str, float] = field(default_factory=dict)
    hyperparams: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "epoch": self.epoch,
            "timestamp": self.timestamp.isoformat(),
            "train_loss": self.train_loss,
            "val_loss": self.val_loss,
            "accuracy": self.accuracy,
            "learning_rate": self.learning_rate,
            "model_hash": self.model_hash[:16] + "...",
            "prev_hash": self.prev_hash[:16] + "...",
            "current_hash": self.current_hash[:16] + "...",
            "signature": self.signature[:16] + "...",
            "status": self.status.value,
            "metrics": self.metrics,
            "hyperparams": self.hyperparams,
            "metadata": self.metadata,
        }
    
    def compute_hash(self) -> str:
        content = json.dumps({
            "record_id": self.record_id,
            "session_id": self.session_id,
            "epoch": self.epoch,
            "timestamp": self.timestamp.isoformat(),
            "train_loss": self.train_loss,
            "val_loss": self.val_loss,
            "accuracy": self.accuracy,
            "learning_rate": self.learning_rate,
            "model_hash": self.model_hash,
            "prev_hash": self.prev_hash,
            "metrics": self.metrics,
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()


class ModelHashCalculator:
    """模型哈希计算器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        self.stats = {
            "total_calculations": 0,
            "cache_hits": 0,
        }
    
    def calculate_hash(
        self,
        model_params: Dict[str, Any],
        include_metadata: bool = True
    ) -> str:
        self.stats["total_calculations"] += 1
        
        if include_metadata:
            content = json.dumps(model_params, sort_keys=True, default=str)
        else:
            if "parameters" in model_params:
                content = json.dumps(model_params["parameters"], sort_keys=True, default=str)
            else:
                content = json.dumps(model_params, sort_keys=True, default=str)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def calculate_partial_hash(
        self,
        layer_params: Dict[str, List[float]]
    ) -> str:
        content = json.dumps(layer_params, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify_hash(
        self,
        model_params: Dict[str, Any],
        expected_hash: str
    ) -> bool:
        calculated = self.calculate_hash(model_params)
        return calculated == expected_hash
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


class TrainingIntegrityVerifier:
    """训练完整性验证器"""
    
    def __init__(self):
        self.verification_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self.stats = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "tampering_detected": 0,
        }
    
    def verify_record(
        self,
        record: TrainingRecord,
        private_key: str = None
    ) -> Tuple[bool, List[str]]:
        self.stats["total_verifications"] += 1
        errors = []
        
        expected_hash = record.compute_hash()
        if record.current_hash != expected_hash:
            errors.append("Hash mismatch - record may have been tampered")
            self.stats["tampering_detected"] += 1
        
        if private_key:
            expected_sig = hashlib.sha256(
                (private_key + record.current_hash).encode()
            ).hexdigest()
            if record.signature != expected_sig:
                errors.append("Signature verification failed")
        
        valid = len(errors) == 0
        
        with self._lock:
            self.verification_history.append({
                "record_id": record.record_id,
                "timestamp": datetime.now().isoformat(),
                "valid": valid,
                "errors": errors,
            })
            
            if valid:
                self.stats["successful_verifications"] += 1
            else:
                self.stats["failed_verifications"] += 1
        
        return valid, errors
    
    def verify_chain(
        self,
        records: List[TrainingRecord]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        all_errors: Dict[str, List[str]] = {}
        all_valid = True
        
        prev_hash = "0" * 64
        
        for record in records:
            errors = []
            
            if record.prev_hash != prev_hash:
                errors.append(f"Chain break: expected {prev_hash[:16]}..., got {record.prev_hash[:16]}...")
                all_valid = False
            
            valid, record_errors = self.verify_record(record)
            if not valid:
                errors.extend(record_errors)
                all_valid = False
            
            if errors:
                all_errors[record.record_id] = errors
            
            prev_hash = record.current_hash
        
        return all_valid, all_errors
    
    def detect_anomalies(
        self,
        records: List[TrainingRecord]
    ) -> List[Dict[str, Any]]:
        anomalies = []
        
        if len(records) < 2:
            return anomalies
        
        losses = [r.train_loss for r in records]
        avg_loss = sum(losses) / len(losses)
        std_loss = (sum((l - avg_loss) ** 2 for l in losses) / len(losses)) ** 0.5
        
        for i, record in enumerate(records):
            if abs(record.train_loss - avg_loss) > 3 * std_loss:
                anomalies.append({
                    "record_id": record.record_id,
                    "epoch": record.epoch,
                    "type": "loss_outlier",
                    "value": record.train_loss,
                    "expected_range": [avg_loss - 3 * std_loss, avg_loss + 3 * std_loss],
                })
            
            if i > 0:
                prev_record = records[i - 1]
                loss_change = abs(record.train_loss - prev_record.train_loss)
                if loss_change > avg_loss * 0.5:
                    anomalies.append({
                        "record_id": record.record_id,
                        "epoch": record.epoch,
                        "type": "sudden_loss_change",
                        "change": loss_change,
                        "prev_loss": prev_record.train_loss,
                        "current_loss": record.train_loss,
                    })
        
        return anomalies
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "verification_history_size": len(self.verification_history),
        }


class TrainingLogger:
    """训练日志记录器主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.private_key = self.config.get(
            "private_key",
            hashlib.sha256(f"key_{time.time()}".encode()).hexdigest()
        )
        
        self.hash_calculator = ModelHashCalculator()
        self.verifier = TrainingIntegrityVerifier()
        
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.records: Dict[str, TrainingRecord] = {}
        self.session_records: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_sessions": 0,
            "total_records": 0,
            "total_epochs_logged": 0,
        }
    
    def start_session(
        self,
        model_name: str,
        hyperparams: Dict[str, Any],
        training_data_hash: str = None
    ) -> str:
        session_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        session = {
            "session_id": session_id,
            "model_name": model_name,
            "hyperparams": hyperparams,
            "training_data_hash": training_data_hash,
            "start_time": datetime.now(),
            "end_time": None,
            "status": TrainingPhase.INIT,
            "best_epoch": 0,
            "best_val_loss": float('inf'),
            "total_epochs": 0,
            "chain_head": "0" * 64,
        }
        
        with self._lock:
            self.sessions[session_id] = session
            self.stats["total_sessions"] += 1
        
        return session_id
    
    def log_epoch(
        self,
        session_id: str,
        epoch: int,
        train_loss: float,
        val_loss: float,
        accuracy: float,
        learning_rate: float,
        model_params: Dict[str, Any] = None,
        metrics: Dict[str, float] = None
    ) -> TrainingRecord:
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
        
        record_id = f"tr_{session_id}_e{epoch}_{uuid.uuid4().hex[:6]}"
        
        model_hash = ""
        if model_params:
            model_hash = self.hash_calculator.calculate_hash(model_params)
        
        prev_hash = session["chain_head"]
        
        record = TrainingRecord(
            record_id=record_id,
            session_id=session_id,
            epoch=epoch,
            timestamp=datetime.now(),
            train_loss=train_loss,
            val_loss=val_loss,
            accuracy=accuracy,
            learning_rate=learning_rate,
            model_hash=model_hash,
            prev_hash=prev_hash,
            current_hash="",
            signature="",
            status=LogStatus.PENDING,
            metrics=metrics or {},
            hyperparams=session["hyperparams"].copy(),
        )
        
        record.current_hash = record.compute_hash()
        record.signature = hashlib.sha256(
            (self.private_key + record.current_hash).encode()
        ).hexdigest()
        record.status = LogStatus.SIGNED
        
        with self._lock:
            self.records[record_id] = record
            self.session_records[session_id].append(record_id)
            
            session["chain_head"] = record.current_hash
            session["total_epochs"] = epoch
            session["status"] = TrainingPhase.TRAINING
            
            if val_loss < session["best_val_loss"]:
                session["best_val_loss"] = val_loss
                session["best_epoch"] = epoch
            
            self.stats["total_records"] += 1
            self.stats["total_epochs_logged"] += 1
        
        return record
    
    def end_session(
        self,
        session_id: str,
        status: TrainingPhase = TrainingPhase.COMPLETED,
        final_metrics: Dict[str, float] = None
    ):
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session["end_time"] = datetime.now()
                session["status"] = status
                session["final_metrics"] = final_metrics or {}
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                return {
                    **session,
                    "start_time": session["start_time"].isoformat(),
                    "end_time": session["end_time"].isoformat() if session["end_time"] else None,
                }
            return None
    
    def get_session_records(
        self,
        session_id: str
    ) -> List[TrainingRecord]:
        with self._lock:
            record_ids = self.session_records.get(session_id, [])
            return [self.records[rid] for rid in record_ids if rid in self.records]
    
    def verify_session(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        records = self.get_session_records(session_id)
        
        if not records:
            return False, {"error": "No records found"}
        
        valid, errors = self.verifier.verify_chain(records)
        
        anomalies = self.verifier.detect_anomalies(records)
        
        return valid, {
            "errors": errors,
            "anomalies": anomalies,
            "total_records": len(records),
        }
    
    def verify_record(self, record_id: str) -> Tuple[bool, List[str]]:
        with self._lock:
            record = self.records.get(record_id)
        
        if not record:
            return False, ["Record not found"]
        
        return self.verifier.verify_record(record, self.private_key)
    
    def export_session(
        self,
        session_id: str,
        include_records: bool = True
    ) -> Dict[str, Any]:
        session = self.get_session(session_id)
        
        if not session:
            return {"error": "Session not found"}
        
        export_data = {
            "session": session,
            "export_time": datetime.now().isoformat(),
        }
        
        if include_records:
            records = self.get_session_records(session_id)
            export_data["records"] = [r.to_dict() for r in records]
        
        return export_data
    
    def get_training_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        records = self.get_session_records(session_id)
        
        return [r.to_dict() for r in records[-limit:]]
    
    def get_loss_curve(
        self,
        session_id: str
    ) -> Dict[str, List[float]]:
        records = self.get_session_records(session_id)
        
        return {
            "epochs": [r.epoch for r in records],
            "train_loss": [r.train_loss for r in records],
            "val_loss": [r.val_loss for r in records],
            "accuracy": [r.accuracy for r in records],
            "learning_rate": [r.learning_rate for r in records],
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "logger": self.stats,
            "hash_calculator": self.hash_calculator.get_stats(),
            "verifier": self.verifier.get_stats(),
            "active_sessions": sum(
                1 for s in self.sessions.values()
                if s["status"] == TrainingPhase.TRAINING
            ),
        }
