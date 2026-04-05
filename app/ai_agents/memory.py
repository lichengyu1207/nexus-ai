"""
MemoryService - 代理记忆与知识库服务
使用ChromaDB作为向量数据库，为每个代理提供长期记忆能力
"""
from typing import List, Dict, Any, Optional
import os
import uuid
from datetime import datetime
import chromadb
from chromadb.config import Settings


class MemoryService:
    """
    记忆服务类 - 单例模式
    为每个代理提供独立的向量知识库
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, persist_directory: str = None):
        """
        初始化记忆服务
        
        Args:
            persist_directory: 数据持久化路径，默认为项目根目录下的data/chroma
        """
        if self._initialized:
            return
        
        # 设置持久化路径
        if persist_directory is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            persist_directory = os.path.join(project_root, 'data', 'chroma')
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self._initialized = True
        print(f"✅ MemoryService initialized with persist directory: {persist_directory}")
    
    def get_or_create_collection(self, agent_name: str) -> Any:
        """
        获取或创建代理专属集合
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Collection: ChromaDB集合对象
        """
        collection_name = f"agent_{agent_name}"
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"agent_name": agent_name, "created_at": datetime.utcnow().isoformat()}
            )
            return collection
        except Exception as e:
            print(f"Error creating collection for {agent_name}: {str(e)}")
            raise
    
    def add_memory(
        self,
        agent_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加记忆（自动向量化）
        
        Args:
            agent_name: 代理名称
            content: 记忆内容
            metadata: 元数据（可选）
            
        Returns:
            str: 记忆ID
        """
        collection = self.get_or_create_collection(agent_name)
        
        # 生成唯一ID
        memory_id = str(uuid.uuid4())
        
        # 准备元数据
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name
        })
        
        # 添加到集合
        try:
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            print(f"✅ Memory added for {agent_name}: {memory_id}")
            return memory_id
            
        except Exception as e:
            print(f"Error adding memory for {agent_name}: {str(e)}")
            raise
    
    def search_memories(
        self,
        agent_name: str,
        query: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            agent_name: 代理名称
            query: 查询文本
            n_results: 返回结果数量
            where_filter: 元数据过滤条件（可选）
            
        Returns:
            List[Dict]: 记忆列表，包含content、metadata、distance
        """
        collection = self.get_or_create_collection(agent_name)
        
        try:
            # 构建查询参数
            query_params = {
                "query_texts": [query],
                "n_results": n_results
            }
            
            # 添加过滤条件
            if where_filter:
                query_params["where"] = where_filter
            
            # 执行查询
            results = collection.query(**query_params)
            
            # 格式化结果
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    memory = {
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"Error searching memories for {agent_name}: {str(e)}")
            return []
    
    def delete_memories(
        self,
        agent_name: str,
        memory_ids: Optional[List[str]] = None,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        删除记忆
        
        Args:
            agent_name: 代理名称
            memory_ids: 记忆ID列表（可选）
            where_filter: 元数据过滤条件（可选）
            
        Returns:
            int: 删除的记忆数量
        """
        collection = self.get_or_create_collection(agent_name)
        
        try:
            if memory_ids:
                # 按ID删除
                collection.delete(ids=memory_ids)
                count = len(memory_ids)
            elif where_filter:
                # 按条件删除
                collection.delete(where=where_filter)
                count = -1  # ChromaDB不返回删除数量
            else:
                # 清空所有记忆
                all_ids = collection.get()['ids']
                if all_ids:
                    collection.delete(ids=all_ids)
                    count = len(all_ids)
                else:
                    count = 0
            
            print(f"✅ Deleted {count} memories for {agent_name}")
            return count
            
        except Exception as e:
            print(f"Error deleting memories for {agent_name}: {str(e)}")
            return 0
    
    def get_memory_count(self, agent_name: str) -> int:
        """
        获取记忆数量
        
        Args:
            agent_name: 代理名称
            
        Returns:
            int: 记忆数量
        """
        collection = self.get_or_create_collection(agent_name)
        try:
            count = collection.count()
            return count
        except Exception as e:
            print(f"Error getting memory count for {agent_name}: {str(e)}")
            return 0
    
    def get_all_memories(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有记忆
        
        Args:
            agent_name: 代理名称
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 记忆列表
        """
        collection = self.get_or_create_collection(agent_name)
        
        try:
            results = collection.get(limit=limit)
            
            memories = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    memory = {
                        "id": results['ids'][i],
                        "content": doc,
                        "metadata": results['metadatas'][i] if results['metadatas'] else {}
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"Error getting all memories for {agent_name}: {str(e)}")
            return []
    
    def cleanup_old_memories(self, agent_name: str, days: int = 30) -> int:
        """
        清理过期记忆
        
        Args:
            agent_name: 代理名称
            days: 保留天数
            
        Returns:
            int: 删除的记忆数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        # 删除早于cutoff_date的记忆
        count = self.delete_memories(
            agent_name,
            where_filter={"timestamp": {"$lt": cutoff_str}}
        )
        
        return count


# 全局单例实例
memory_service = MemoryService()
