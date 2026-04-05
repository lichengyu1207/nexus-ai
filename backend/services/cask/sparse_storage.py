# -*- coding: utf-8 -*-
"""
CASK 稀疏存储管理器模块
实现分块存储和CSR压缩格式
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from uuid import UUID, uuid4
import json

from .config import CASKConfig
from .models import KVCacheBlock, ImportanceScore


@dataclass
class CSRFormat:
    values: List[float] = field(default_factory=list)
    col_indices: List[int] = field(default_factory=list)
    row_ptr: List[int] = field(default_factory=list)
    shape: Tuple[int, int] = (0, 0)
    
    def to_dense(self) -> List[List[float]]:
        if not self.values:
            return []
        
        rows, cols = self.shape
        dense = [[0.0] * cols for _ in range(rows)]
        
        for i in range(len(self.row_ptr) - 1):
            start = self.row_ptr[i]
            end = self.row_ptr[i + 1]
            for j in range(start, end):
                if j < len(self.col_indices) and j < len(self.values):
                    col = self.col_indices[j]
                    if col < cols:
                        dense[i][col] = self.values[j]
        
        return dense
    
    @classmethod
    def from_dense(cls, dense: List[List[float]]) -> 'CSRFormat':
        if not dense:
            return CSRFormat()
        
        rows = len(dense)
        cols = len(dense[0]) if dense else 0
        
        values = []
        col_indices = []
        row_ptr = [0]
        
        for row in dense:
            for col, val in enumerate(row):
                if val != 0:
                    values.append(val)
                    col_indices.append(col)
            row_ptr.append(len(values))
        
        return CSRFormat(
            values=values,
            col_indices=col_indices,
            row_ptr=row_ptr,
            shape=(rows, cols)
        )
    
    def to_dict(self) -> Dict:
        return {
            "values": self.values,
            "col_indices": self.col_indices,
            "row_ptr": self.row_ptr,
            "shape": list(self.shape)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CSRFormat':
        return cls(
            values=data.get("values", []),
            col_indices=data.get("col_indices", []),
            row_ptr=data.get("row_ptr", []),
            shape=tuple(data.get("shape", [0, 0]))
        )
    
    def get_nnz(self) -> int:
        return len(self.values)
    
    def get_sparsity(self) -> float:
        rows, cols = self.shape
        if rows * cols == 0:
            return 0.0
        return 1.0 - self.get_nnz() / (rows * cols)


@dataclass
class Block:
    id: UUID = field(default_factory=uuid4)
    block_index: int = 0
    start_position: int = 0
    end_position: int = 0
    data: List[Tuple[List[float], List[float]]] = field(default_factory=list)
    csr_format: Optional[CSRFormat] = None
    avg_importance: float = 0.0
    is_sparse: bool = False
    
    def get_token_count(self) -> int:
        return len(self.data)
    
    def to_kv_cache_block(self, session_id: UUID, sparsity_rate: float = 0.0) -> KVCacheBlock:
        csr_dict = self.csr_format.to_dict() if self.csr_format else {}
        
        return KVCacheBlock(
            session_id=session_id,
            block_index=self.block_index,
            start_position=self.start_position,
            end_position=self.end_position,
            compressed_data={"size": len(self.data)},
            csr_values=csr_dict.get("values", []),
            csr_col_indices=csr_dict.get("col_indices", []),
            csr_row_ptr=csr_dict.get("row_ptr", []),
            avg_importance=self.avg_importance,
            token_count=len(self.data),
            is_sparse=self.is_sparse,
            sparsity_rate=sparsity_rate
        )


class BlockManager:
    def __init__(self, block_size: int = 64):
        self.block_size = block_size
        self.blocks: List[Block] = []
        self._next_block_index = 0
    
    def allocate_block(self) -> Block:
        block = Block(
            block_index=self._next_block_index,
            start_position=self._next_block_index * self.block_size,
            end_position=(self._next_block_index + 1) * self.block_size
        )
        self._next_block_index += 1
        self.blocks.append(block)
        return block
    
    def free_block(self, block_id: UUID) -> bool:
        for i, block in enumerate(self.blocks):
            if block.id == block_id:
                self.blocks.pop(i)
                return True
        return False
    
    def get_block(self, block_index: int) -> Optional[Block]:
        for block in self.blocks:
            if block.block_index == block_index:
                return block
        return None
    
    def get_blocks_for_range(self, start: int, end: int) -> List[Block]:
        result = []
        for block in self.blocks:
            if block.end_position >= start and block.start_position <= end:
                result.append(block)
        return result
    
    def get_total_tokens(self) -> int:
        return sum(block.get_token_count() for block in self.blocks)
    
    def clear(self):
        self.blocks = []
        self._next_block_index = 0


class SparseStorage:
    def __init__(self, config: CASKConfig):
        self.config = config
        self.block_manager = BlockManager(block_size=config.block_size)
        self._current_block: Optional[Block] = None
        self._position_counter = 0
    
    def store(
        self, 
        kv_pairs: List[Tuple[List[float], List[float]]],
        importance_scores: List[ImportanceScore],
        selected_indices: List[int],
        session_id: UUID
    ) -> List[KVCacheBlock]:
        blocks = []
        
        sparse_kv = [kv_pairs[i] for i in selected_indices if i < len(kv_pairs)]
        
        for i, (k, v) in enumerate(sparse_kv):
            if self._current_block is None or len(self._current_block.data) >= self.config.block_size:
                if self._current_block is not None:
                    self._finalize_block(self._current_block, importance_scores, session_id)
                    blocks.append(self._current_block.to_kv_cache_block(
                        session_id, 
                        self._calculate_block_sparsity(self._current_block, len(kv_pairs))
                    ))
                
                self._current_block = self.block_manager.allocate_block()
            
            self._current_block.data.append((k, v))
            self._position_counter += 1
        
        if self._current_block and self._current_block.data:
            self._finalize_block(self._current_block, importance_scores, session_id)
            blocks.append(self._current_block.to_kv_cache_block(
                session_id,
                self._calculate_block_sparsity(self._current_block, len(kv_pairs))
            ))
        
        return blocks
    
    def _finalize_block(
        self, 
        block: Block, 
        importance_scores: List[ImportanceScore],
        session_id: UUID
    ):
        if not block.data:
            return
        
        dense = self._kv_to_dense(block.data)
        block.csr_format = CSRFormat.from_dense(dense)
        block.is_sparse = block.csr_format.get_sparsity() > 0.1
        
        if importance_scores:
            start_idx = block.start_position
            end_idx = min(block.end_position, len(importance_scores))
            relevant_scores = [s.combined_score for s in importance_scores[start_idx:end_idx]]
            block.avg_importance = sum(relevant_scores) / len(relevant_scores) if relevant_scores else 0.0
    
    def _kv_to_dense(self, kv_pairs: List[Tuple[List[float], List[float]]]) -> List[List[float]]:
        if not kv_pairs:
            return []
        
        dim = len(kv_pairs[0][0]) if kv_pairs[0] else 0
        dense = []
        
        for k, v in kv_pairs:
            combined = k + v
            dense.append(combined)
        
        return dense
    
    def _calculate_block_sparsity(self, block: Block, total_kv: int) -> float:
        if total_kv == 0:
            return 0.0
        return 1.0 - len(block.data) / total_kv
    
    def retrieve(self, indices: List[int]) -> List[Tuple[List[float], List[float]]]:
        result = []
        
        for idx in indices:
            block_idx = idx // self.config.block_size
            local_idx = idx % self.config.block_size
            
            block = self.block_manager.get_block(block_idx)
            if block and local_idx < len(block.data):
                result.append(block.data[local_idx])
        
        return result
    
    def retrieve_block(self, block_index: int) -> Optional[Block]:
        return self.block_manager.get_block(block_index)
    
    def get_all_blocks(self) -> List[Block]:
        return self.block_manager.blocks
    
    def get_total_kv_pairs(self) -> int:
        return sum(block.get_token_count() for block in self.block_manager.blocks)
    
    def get_memory_usage(self, hidden_dim: int = 4096, precision_bytes: int = 2) -> float:
        total_pairs = self.get_total_kv_pairs()
        bytes_per_kv = 2 * hidden_dim * precision_bytes
        return total_pairs * bytes_per_kv / (1024 * 1024)
    
    def compress(self) -> Dict:
        return {
            "blocks": [
                {
                    "block_index": b.block_index,
                    "start_position": b.start_position,
                    "end_position": b.end_position,
                    "csr": b.csr_format.to_dict() if b.csr_format else None,
                    "avg_importance": b.avg_importance,
                    "is_sparse": b.is_sparse,
                    "token_count": b.get_token_count()
                }
                for b in self.block_manager.blocks
            ],
            "total_tokens": self.get_total_kv_pairs(),
            "config": self.config.to_dict()
        }
    
    def clear(self):
        self.block_manager.clear()
        self._current_block = None
        self._position_counter = 0
    
    def update_config(self, config: CASKConfig):
        self.config = config
        self.block_manager = BlockManager(block_size=config.block_size)
