"""
审计日志完整性验证智能体
确保审计日志不可篡改
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IntegrityStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    TAMPERED = "tampered"
    MISSING = "missing"


class HashChain(BaseModel):
    chain_id: str = Field(default_factory=lambda: str(uuid4()))
    block_count: int = 0
    last_hash: str = ""
    merkle_root: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class IntegrityBlock(BaseModel):
    block_id: str = Field(default_factory=lambda: str(uuid4()))
    index: int
    timestamp: datetime
    log_id: str
    log_hash: str
    previous_hash: str
    current_hash: str
    nonce: int = 0
    merkle_proof: List[str] = Field(default_factory=list)


class IntegrityCheckResult(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    chain_id: str
    status: IntegrityStatus
    blocks_checked: int = 0
    invalid_blocks: List[int] = Field(default_factory=list)
    tampered_blocks: List[int] = Field(default_factory=list)
    missing_blocks: List[int] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class MerkleTree:
    def __init__(self):
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def build(self, hashes: List[str]) -> str:
        if not hashes:
            return ""
        
        self.leaves = hashes.copy()
        self.tree = [self.leaves.copy()]
        
        current_level = self.leaves.copy()
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                    next_hash = hashlib.sha256(combined.encode()).hexdigest()
                else:
                    next_hash = current_level[i]
                next_level.append(next_hash)
            
            self.tree.append(next_level)
            current_level = next_level
        
        return current_level[0] if current_level else ""
    
    def get_proof(self, index: int) -> List[str]:
        if index >= len(self.leaves):
            return []
        
        proof = []
        current_index = index
        
        for level in self.tree[:-1]:
            sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
            
            if sibling_index < len(level):
                proof.append(level[sibling_index])
            
            current_index = current_index // 2
        
        return proof
    
    def verify_proof(
        self,
        leaf_hash: str,
        proof: List[str],
        root_hash: str,
        index: int
    ) -> bool:
        current_hash = leaf_hash
        
        for i, sibling_hash in enumerate(proof):
            if (index >> i) % 2 == 0:
                combined = current_hash + sibling_hash
            else:
                combined = sibling_hash + current_hash
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == root_hash


class HashChainManager:
    DIFFICULTY = 4
    
    def __init__(self):
        self.chains: Dict[str, HashChain] = {}
        self.blocks: Dict[str, List[IntegrityBlock]] = {}
        self.main_chain_id = "main_audit_chain"
        
        self._init_main_chain()
    
    def _init_main_chain(self):
        genesis_block = IntegrityBlock(
            index=0,
            timestamp=datetime.now(),
            log_id="genesis",
            log_hash="0" * 64,
            previous_hash="0" * 64,
            current_hash="",
            nonce=0
        )
        
        genesis_block.current_hash = self._compute_hash(genesis_block)
        
        self.chains[self.main_chain_id] = HashChain(
            chain_id=self.main_chain_id,
            block_count=1,
            last_hash=genesis_block.current_hash
        )
        
        self.blocks[self.main_chain_id] = [genesis_block]
    
    def add_block(
        self,
        log_id: str,
        log_data: Dict[str, Any],
        chain_id: Optional[str] = None
    ) -> IntegrityBlock:
        chain_id = chain_id or self.main_chain_id
        
        if chain_id not in self.chains:
            self.chains[chain_id] = HashChain(chain_id=chain_id)
            self.blocks[chain_id] = []
        
        chain = self.chains[chain_id]
        blocks = self.blocks[chain_id]
        
        log_hash = self._hash_log(log_data)
        
        block = IntegrityBlock(
            index=len(blocks),
            timestamp=datetime.now(),
            log_id=log_id,
            log_hash=log_hash,
            previous_hash=chain.last_hash
        )
        
        block.nonce = self._mine_block(block)
        block.current_hash = self._compute_hash(block)
        
        blocks.append(block)
        
        chain.block_count = len(blocks)
        chain.last_hash = block.current_hash
        chain.updated_at = datetime.now()
        
        return block
    
    def _hash_log(self, log_data: Dict[str, Any]) -> str:
        log_str = json.dumps(log_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(log_str.encode()).hexdigest()
    
    def _compute_hash(self, block: IntegrityBlock) -> str:
        block_data = {
            "index": block.index,
            "timestamp": block.timestamp.isoformat(),
            "log_id": block.log_id,
            "log_hash": block.log_hash,
            "previous_hash": block.previous_hash,
            "nonce": block.nonce
        }
        
        block_str = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()
    
    def _mine_block(self, block: IntegrityBlock) -> int:
        nonce = 0
        target = "0" * self.DIFFICULTY
        
        while True:
            block.nonce = nonce
            hash_result = self._compute_hash(block)
            
            if hash_result.startswith(target):
                return nonce
            
            nonce += 1
            
            if nonce > 1000000:
                break
        
        return nonce
    
    def verify_chain(self, chain_id: Optional[str] = None) -> IntegrityCheckResult:
        chain_id = chain_id or self.main_chain_id
        
        if chain_id not in self.chains:
            return IntegrityCheckResult(
                chain_id=chain_id,
                status=IntegrityStatus.MISSING,
                details={"error": "Chain not found"}
            )
        
        blocks = self.blocks.get(chain_id, [])
        invalid_blocks = []
        tampered_blocks = []
        
        for i, block in enumerate(blocks):
            if i == 0:
                continue
            
            if block.previous_hash != blocks[i - 1].current_hash:
                invalid_blocks.append(i)
            
            computed_hash = self._compute_hash(block)
            if computed_hash != block.current_hash:
                tampered_blocks.append(i)
        
        status = IntegrityStatus.VALID
        if invalid_blocks or tampered_blocks:
            status = IntegrityStatus.TAMPERED if tampered_blocks else IntegrityStatus.INVALID
        
        return IntegrityCheckResult(
            chain_id=chain_id,
            status=status,
            blocks_checked=len(blocks),
            invalid_blocks=invalid_blocks,
            tampered_blocks=tampered_blocks
        )
    
    def get_block(self, index: int, chain_id: Optional[str] = None) -> Optional[IntegrityBlock]:
        chain_id = chain_id or self.main_chain_id
        
        blocks = self.blocks.get(chain_id, [])
        
        if 0 <= index < len(blocks):
            return blocks[index]
        
        return None
    
    def get_chain_info(self, chain_id: Optional[str] = None) -> Dict[str, Any]:
        chain_id = chain_id or self.main_chain_id
        
        chain = self.chains.get(chain_id)
        if not chain:
            return {}
        
        blocks = self.blocks.get(chain_id, [])
        
        return {
            "chain_id": chain_id,
            "block_count": chain.block_count,
            "last_hash": chain.last_hash,
            "created_at": chain.created_at.isoformat(),
            "updated_at": chain.updated_at.isoformat(),
            "first_block_hash": blocks[0].current_hash if blocks else None
        }


class AuditIntegrityAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "AuditIntegrity",
        storage: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.storage = storage
        
        self.chain_manager = HashChainManager()
        self.merkle_tree = MerkleTree()
        
        self.check_interval = timedelta(hours=1)
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"AuditIntegrityAgent {self.agent_id} initialized")
    
    async def seal_log(self, log_data: Dict[str, Any]) -> IntegrityBlock:
        log_id = log_data.get("id", str(uuid4()))
        
        block = self.chain_manager.add_block(log_id, log_data)
        
        self.logger.debug(f"Sealed log {log_id} in block {block.index}")
        
        return block
    
    async def batch_seal(self, logs: List[Dict[str, Any]]) -> List[IntegrityBlock]:
        blocks = []
        
        for log_data in logs:
            block = await self.seal_log(log_data)
            blocks.append(block)
        
        return blocks
    
    async def verify_log_integrity(
        self,
        log_id: str,
        log_data: Dict[str, Any],
        block_index: int
    ) -> bool:
        block = self.chain_manager.get_block(block_index)
        
        if not block:
            return False
        
        if block.log_id != log_id:
            return False
        
        computed_hash = self.chain_manager._hash_log(log_data)
        
        return computed_hash == block.log_hash
    
    async def verify_full_chain(self) -> IntegrityCheckResult:
        result = self.chain_manager.verify_chain()
        
        if result.status != IntegrityStatus.VALID:
            self.logger.error(
                f"Chain integrity check failed: {result.status.value}, "
                f"invalid: {result.invalid_blocks}, tampered: {result.tampered_blocks}"
            )
            
            await self._alert_integrity_violation(result)
        
        return result
    
    async def _alert_integrity_violation(self, result: IntegrityCheckResult):
        self.logger.critical(
            f"INTEGRITY VIOLATION DETECTED: {result.status.value}"
        )
    
    async def build_merkle_proof(
        self,
        block_indices: List[int]
    ) -> Dict[str, Any]:
        blocks = self.chain_manager.blocks.get(
            self.chain_manager.main_chain_id, []
        )
        
        hashes = [block.current_hash for block in blocks]
        
        merkle_root = self.merkle_tree.build(hashes)
        
        proofs = {}
        for index in block_indices:
            if 0 <= index < len(blocks):
                proofs[index] = {
                    "block_hash": blocks[index].current_hash,
                    "merkle_proof": self.merkle_tree.get_proof(index)
                }
        
        return {
            "merkle_root": merkle_root,
            "proofs": proofs
        }
    
    async def verify_merkle_proof(
        self,
        block_index: int,
        block_hash: str,
        merkle_proof: List[str],
        merkle_root: str
    ) -> bool:
        return self.merkle_tree.verify_proof(
            block_hash,
            merkle_proof,
            merkle_root,
            block_index
        )
    
    async def get_chain_statistics(self) -> Dict[str, Any]:
        chain_info = self.chain_manager.get_chain_info()
        
        blocks = self.chain_manager.blocks.get(
            self.chain_manager.main_chain_id, []
        )
        
        if not blocks:
            return chain_info
        
        timestamps = [b.timestamp for b in blocks]
        
        return {
            **chain_info,
            "earliest_block": min(timestamps).isoformat(),
            "latest_block": max(timestamps).isoformat(),
            "avg_block_interval": self._compute_avg_interval(blocks)
        }
    
    def _compute_avg_interval(self, blocks: List[IntegrityBlock]) -> float:
        if len(blocks) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(blocks)):
            delta = (blocks[i].timestamp - blocks[i-1].timestamp).total_seconds()
            intervals.append(delta)
        
        return sum(intervals) / len(intervals) if intervals else 0.0
    
    async def start_continuous_verification(self):
        self._running = True
        asyncio.create_task(self._verification_loop())
    
    async def stop_continuous_verification(self):
        self._running = False
    
    async def _verification_loop(self):
        while self._running:
            try:
                result = await self.verify_full_chain()
                
                self.logger.info(
                    f"Chain verification completed: {result.status.value}, "
                    f"blocks checked: {result.blocks_checked}"
                )
                
                await asyncio.sleep(self.check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in verification loop: {e}")
                await asyncio.sleep(60)
    
    def get_statistics(self) -> Dict[str, Any]:
        chain_info = self.chain_manager.get_chain_info()
        
        return {
            "chain_info": chain_info,
            "running": self._running
        }
