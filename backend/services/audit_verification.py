"""
审计日志验证服务
支持哈希链验证和数字签名
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class VerificationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class VerificationResult:
    status: VerificationStatus
    total_logs: int
    verified_logs: int
    hash_errors: List[Dict[str, Any]]
    chain_errors: List[Dict[str, Any]]
    signature_errors: List[Dict[str, Any]]
    verification_time: datetime
    duration_ms: float


class AuditVerification:
    GENESIS_HASH = "0" * 64
    
    def __init__(self):
        self._private_key = None
        self._public_key = None
        self._keys_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "keys")
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        if not CRYPTO_AVAILABLE:
            logger.warning("Cryptography library not available, signing disabled")
            return
        
        try:
            os.makedirs(self._keys_dir, exist_ok=True)
            private_key_path = os.path.join(self._keys_dir, "audit_private.pem")
            public_key_path = os.path.join(self._keys_dir, "audit_public.pem")
            
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                with open(private_key_path, "rb") as f:
                    self._private_key = serialization.load_pem_private_key(
                        f.read(), password=None, backend=default_backend()
                    )
                with open(public_key_path, "rb") as f:
                    self._public_key = serialization.load_pem_public_key(
                        f.read(), backend=default_backend()
                    )
            else:
                self._private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                self._public_key = self._private_key.public_key()
                
                with open(private_key_path, "wb") as f:
                    f.write(self._private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                with open(public_key_path, "wb") as f:
                    f.write(self._public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
            
            logger.info("Audit signing keys loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load/generate audit keys: {e}")
            self._private_key = None
            self._public_key = None
    
    def compute_hash(self, log: Dict[str, Any]) -> str:
        data = json.dumps(log, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def compute_batch_hash(self, logs: List[Dict[str, Any]]) -> str:
        combined = "".join(self.compute_hash(log) for log in logs)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def sign_batch(self, batch_hash: str) -> Optional[str]:
        if not CRYPTO_AVAILABLE or not self._private_key:
            return None
        
        try:
            signature = self._private_key.sign(
                batch_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign batch: {e}")
            return None
    
    def verify_signature(self, batch_hash: str, signature: str) -> bool:
        if not CRYPTO_AVAILABLE or not self._public_key:
            return False
        
        try:
            self._public_key.verify(
                bytes.fromhex(signature),
                batch_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def verify_chain(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
        limit: int = 10000,
        verify_signatures: bool = True
    ) -> VerificationResult:
        from ..database import get_db
        
        start_time = datetime.utcnow()
        
        try:
            async with get_db() as conn:
                query = "SELECT * FROM audit_logs WHERE 1=1"
                params = []
                
                if start_id:
                    query += " AND id >= ?"
                    params.append(start_id)
                if end_id:
                    query += " AND id <= ?"
                    params.append(end_id)
                
                query += " ORDER BY timestamp ASC LIMIT ?"
                params.append(limit)
                
                cursor = await conn.execute(query, params)
                logs = await cursor.fetchall()
        except Exception as e:
            logger.error(f"Database error in verify_chain: {e}")
            return VerificationResult(
                status=VerificationStatus.ERROR,
                total_logs=0,
                verified_logs=0,
                hash_errors=[],
                chain_errors=[],
                signature_errors=[],
                verification_time=start_time,
                duration_ms=0
            )
        
        if not logs:
            return VerificationResult(
                status=VerificationStatus.VALID,
                total_logs=0,
                verified_logs=0,
                hash_errors=[],
                chain_errors=[],
                signature_errors=[],
                verification_time=start_time,
                duration_ms=0
            )
        
        hash_errors = []
        chain_errors = []
        signature_errors = []
        prev_hash = self.GENESIS_HASH
        
        for i, log in enumerate(logs):
            log_dict = dict(log)
            computed_hash = self.compute_hash(log_dict)
            
            if "hash" in log_dict and log_dict["hash"] != computed_hash:
                hash_errors.append({
                    "log_id": log_dict.get("id"),
                    "expected": computed_hash,
                    "actual": log_dict.get("hash")
                })
            
            if "prev_hash" in log_dict and log_dict["prev_hash"] != prev_hash:
                chain_errors.append({
                    "log_id": log_dict.get("id"),
                    "expected": prev_hash,
                    "actual": log_dict["prev_hash"]
                })
            
            prev_hash = computed_hash
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        status = VerificationStatus.VALID
        if hash_errors or chain_errors:
            status = VerificationStatus.INVALID
        elif signature_errors:
            status = VerificationStatus.WARNING
        
        return VerificationResult(
            status=status,
            total_logs=len(logs),
            verified_logs=len(logs) - len(hash_errors) - len(chain_errors),
            hash_errors=hash_errors,
            chain_errors=chain_errors,
            signature_errors=signature_errors,
            verification_time=start_time,
            duration_ms=duration_ms
        )
    
    async def sign_unbatched_logs(self, batch_size: int = 100) -> int:
        from ..database import get_db
        
        if not CRYPTO_AVAILABLE or not self._private_key:
            logger.warning("Signing not available")
            return 0
        
        try:
            async with get_db() as conn:
                cursor = await conn.execute("""
                    SELECT end_log_id FROM audit_signature_batches
                    ORDER BY end_timestamp DESC LIMIT 1
                """)
                last_signed = await cursor.fetchone()
                
                if last_signed:
                    cursor = await conn.execute("""
                        SELECT * FROM audit_logs
                        WHERE id > ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    """, (last_signed["end_log_id"], batch_size))
                    logs = await cursor.fetchall()
                else:
                    cursor = await conn.execute("""
                        SELECT * FROM audit_logs
                        ORDER BY timestamp ASC
                        LIMIT ?
                    """, (batch_size,))
                    logs = await cursor.fetchall()
        except Exception as e:
            logger.error(f"Database error in sign_unbatched_logs: {e}")
            return 0
        
        if not logs:
            return 0
        
        logs_list = [dict(log) for log in logs]
        batch_hash = self.compute_batch_hash(logs_list)
        signature = self.sign_batch(batch_hash)
        
        if not signature:
            return 0
        
        return len(logs)


audit_verification = AuditVerification()
