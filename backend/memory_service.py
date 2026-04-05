"""
代理记忆服务
使用简单的文件存储实现记忆功能（兼容性版本）
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging
from pathlib import Path
import hashlib
import os

logger = logging.getLogger(__name__)

MEMORY_PATH = Path(__file__).parent.parent / "data" / "memories"


class MemoryService:
    """
    代理记忆服务
    为代理提供长期记忆存储和相似性检索能力
    使用简单的文件存储实现
    """
    
    def __init__(self, persist_directory: str = None):
        """
        初始化记忆服务
        
        Args:
            persist_directory: 持久化目录
        """
        self.persist_directory = persist_directory or str(MEMORY_PATH)
        
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._load_memories()
        
        logger.info(f"MemoryService initialized with {len(self._memories)} memories")
    
    def _load_memories(self):
        """从文件加载记忆"""
        memory_file = Path(self.persist_directory) / "memories.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    self._memories = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load memories: {e}")
                self._memories = {}
    
    def _save_memories(self):
        """保存记忆到文件"""
        memory_file = Path(self.persist_directory) / "memories.json"
        try:
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self._memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def store_memory(
        self,
        agent_name: str,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        存储记忆
        
        Args:
            agent_name: 代理名称
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            str: 记忆ID
        """
        memory_id = str(uuid.uuid4())
        
        full_metadata = {
            "agent_name": agent_name,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self._memories[memory_id] = {
            "id": memory_id,
            "content": content,
            "metadata": full_metadata
        }
        
        self._save_memories()
        
        logger.debug(f"Stored memory {memory_id} for agent {agent_name}")
        
        return memory_id
    
    async def search_memories(
        self,
        query: str,
        agent_name: str = None,
        memory_type: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相似记忆
        
        Args:
            query: 查询文本
            agent_name: 代理名称过滤
            memory_type: 记忆类型过滤
            n_results: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        results = []
        
        for memory_id, memory in self._memories.items():
            metadata = memory.get("metadata", {})
            
            if agent_name and metadata.get("agent_name") != agent_name:
                continue
            
            if memory_type and metadata.get("memory_type") != memory_type:
                continue
            
            similarity = self._simple_similarity(query, memory.get("content", ""))
            
            results.append({
                "id": memory_id,
                "content": memory.get("content"),
                "metadata": metadata,
                "distance": 1 - similarity
            })
        
        results.sort(key=lambda x: x["distance"])
        
        logger.debug(f"Found {len(results[:n_results])} memories for query")
        
        return results[:n_results]
    
    async def get_agent_memories(
        self,
        agent_name: str,
        memory_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取代理的所有记忆
        
        Args:
            agent_name: 代理名称
            memory_type: 记忆类型过滤
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 记忆列表
        """
        results = []
        
        for memory_id, memory in self._memories.items():
            metadata = memory.get("metadata", {})
            
            if metadata.get("agent_name") != agent_name:
                continue
            
            if memory_type and metadata.get("memory_type") != memory_type:
                continue
            
            results.append({
                "id": memory_id,
                "content": memory.get("content"),
                "metadata": metadata
            })
        
        return results[:limit]
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save_memories()
            logger.debug(f"Deleted memory {memory_id}")
            return True
        return False
    
    async def clear_agent_memories(self, agent_name: str) -> int:
        """
        清除代理的所有记忆
        
        Args:
            agent_name: 代理名称
            
        Returns:
            int: 删除的记忆数量
        """
        to_delete = [
            mid for mid, mem in self._memories.items()
            if mem.get("metadata", {}).get("agent_name") == agent_name
        ]
        
        for mid in to_delete:
            del self._memories[mid]
        
        self._save_memories()
        
        logger.info(f"Cleared {len(to_delete)} memories for agent {agent_name}")
        
        return len(to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_memories": len(self._memories),
            "persist_directory": self.persist_directory
        }


memory_service = MemoryService()
