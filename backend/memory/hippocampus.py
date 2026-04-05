"""
海马体记忆系统 - 三层结构实现（ReMemR1可回溯增强版）
Hippocampus Memory System with Three-Tier Architecture

负责存储用户请求、中间处理数据和最终结果，并更新用户画像。

三层结构：
1. 工作记忆：存储在Redis中，保存当前会话的上下文，有效期24小时
2. 短期记忆：存储为向量形式（使用ChromaDB），保存30天内的交互记录，支持相似度检索
3. 长期记忆：压缩存储历史数据，基于访问频率和艾宾浩斯遗忘曲线自动清理低价值记忆

集成ReMemR1（Shi et al., 2026）：非线性可回溯记忆检索与多级奖励设计
"""

import os
import json
import time
import logging
import hashlib
import pickle
import gzip
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

# 延迟导入可能不兼容的库
redis = None
chromadb = None
Settings = None
transformers = None
BertTokenizer = None
BertModel = None
neo4j = None
graph_db = None

try:
    import redis
except Exception as e:
    logging.warning(f"Redis导入失败: {e}")

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    logging.warning(f"ChromaDB导入失败: {e}")

try:
    from transformers import BertTokenizer, BertModel
    import torch
except Exception as e:
    logging.warning(f"BERT模型导入失败: {e}")

try:
    from neo4j import GraphDatabase
except Exception as e:
    logging.warning(f"Neo4j导入失败: {e}")

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    user_id: str
    request: Dict[str, Any]
    intermediate_data: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    importance: float = 1.0  # 初始重要性
    marked_for_deletion: bool = False  # 是否标记为待删除
    deletion_buffer_start: float = 0.0  # 删除缓冲期开始时间


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: Dict[str, Any]
    interaction_history: List[str]
    last_updated: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalNode:
    """ReMemR1检索节点 - 用于非线性检索路径追踪"""
    node_id: str
    memory: MemoryItem
    source_layer: str  # "working", "short_term", "long_term"
    similarity_score: float
    retrieval_depth: int = 0
    parent_node_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    revisited_count: int = 0
    reward_signal: float = 0.0
    timestamp: float = field(default_factory=time.time)
    backtracked: bool = False


@dataclass
class RetrievalPath:
    """ReMemR1检索路径 - 支持非线性回溯"""
    path_id: str
    query: Dict[str, Any]
    nodes: List[RetrievalNode] = field(default_factory=list)
    current_position: int = 0
    is_complete: bool = False
    total_reward: float = 0.0
    backtrack_count: int = 0
    created_at: float = field(default_factory=time.time)

    def add_node(self, node: RetrievalNode):
        self.nodes.append(node)
        if len(self.nodes) > 1:
            node.parent_node_id = self.nodes[-2].node_id
            self.nodes[-2].children_ids.append(node.node_id)

    def can_backtrack(self) -> bool:
        return self.current_position > 0

    def backtrack(self) -> Optional[RetrievalNode]:
        if not self.can_backtrack():
            return None
        self.current_position -= 1
        self.backtrack_count += 1
        if self.current_position < len(self.nodes):
            node = self.nodes[self.current_position]
            node.revisited_count += 1
            node.backtracked = True
            return node
        return None

    def get_current_node(self) -> Optional[RetrievalNode]:
        if 0 <= self.current_position < len(self.nodes):
            return self.nodes[self.current_position]
        return None

    def advance(self):
        if self.current_position < len(self.nodes) - 1:
            self.current_position += 1


@dataclass
class MemoryReward:
    """ReMemR1多级奖励设计"""
    hit_reward: float = 1.0
    precision_bonus: float = 0.5
    recall_bonus: float = 0.3
    serendipity_bonus: float = 0.8
    revisit_penalty: float = -0.1
    backtrack_cost: float = -0.05
    novelty_bonus: float = 0.4
    relevance_weight: float = 0.6


class Hippocampus:
    """海马体记忆系统"""
    
    def __init__(self, storage_path: str = None):
        # 存储路径
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "memory"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 工作记忆阈值
        self.working_memory_threshold = 100
        
        # 初始化BERT模型
        self._init_bert_model()
        
        # 三层存储初始化
        self._init_working_memory()  # 工作记忆（Redis）
        self._init_short_term_memory()  # 短期记忆（ChromaDB）
        self._init_long_term_memory()  # 长期记忆（Neo4j/压缩存储）
        
        # 定期清理任务
        self._schedule_cleanup()
        
        # 定期固化任务
        self._schedule_consolidation()

        # ReMemR1可回溯记忆系统（Shi et al., 2026）
        self._retrieval_paths: Dict[str, RetrievalPath] = {}
        self._reward_config = MemoryReward()
        self._retrieval_stats = {
            "total_retrievals": 0,
            "avg_path_length": 0.0,
            "backtrack_rate": 0.0,
            "avg_reward": 0.0,
            "novelty_discoveries": 0,
        }
        self._max_backtrack_depth = 3
        self._revisit_threshold = 2
    
    def _init_working_memory(self):
        """初始化工作记忆（Redis）"""
        try:
            if redis:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("工作记忆（Redis）初始化成功")
            else:
                raise ImportError("Redis not available")
        except Exception as e:
            logger.warning(f"工作记忆（Redis）初始化失败，将使用内存存储: {e}")
            self.redis_client = None
            self.working_memory = {}
    
    def _init_bert_model(self):
        """初始化BERT模型"""
        try:
            if BertTokenizer and BertModel:
                self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
                self.bert_model = BertModel.from_pretrained('bert-base-chinese')
                self.bert_model.eval()
                logger.info("BERT模型初始化成功")
            else:
                raise ImportError("BERT model not available")
        except Exception as e:
            logger.warning(f"BERT模型初始化失败，将使用字符频率嵌入: {e}")
            self.tokenizer = None
            self.bert_model = None
    
    def _init_short_term_memory(self):
        """初始化短期记忆（ChromaDB）"""
        try:
            if chromadb and Settings:
                self.chroma_client = chromadb.Client(
                    settings=Settings(
                        persist_directory=os.path.join(self.storage_path, "chromadb")
                    )
                )
                self.memory_collection = self.chroma_client.get_or_create_collection(
                    name="memories",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("短期记忆（ChromaDB）初始化成功")
            else:
                raise ImportError("ChromaDB not available")
        except Exception as e:
            logger.warning(f"短期记忆（ChromaDB）初始化失败，将使用内存存储: {e}")
            self.chroma_client = None
            self.short_term_memory = {}
    
    def _init_long_term_memory(self):
        """初始化长期记忆（Neo4j/压缩存储）"""
        # 尝试初始化Neo4j连接
        self.neo4j_driver = None
        try:
            if GraphDatabase:
                self.neo4j_driver = GraphDatabase.driver(
                    "bolt://localhost:7687",
                    auth=("neo4j", "password")  # 默认凭证，实际使用时应配置
                )
                # 测试连接
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                logger.info("长期记忆（Neo4j）初始化成功")
            else:
                raise ImportError("Neo4j not available")
        except Exception as e:
            logger.warning(f"长期记忆（Neo4j）初始化失败，将使用压缩存储: {e}")
            self.neo4j_driver = None
        
        # 初始化压缩存储作为备份
        self.long_term_memory_dir = os.path.join(self.storage_path, "long_term")
        os.makedirs(self.long_term_memory_dir, exist_ok=True)
        self.long_term_memory = {}
        self._load_long_term_memory()
        logger.info("长期记忆（压缩存储）初始化成功")
    
    def _load_long_term_memory(self):
        """加载长期记忆"""
        try:
            for filename in os.listdir(self.long_term_memory_dir):
                if filename.endswith(".gz"):
                    file_path = os.path.join(self.long_term_memory_dir, filename)
                    with gzip.open(file_path, 'rb') as f:
                        memories = pickle.load(f)
                        self.long_term_memory.update(memories)
        except Exception as e:
            logger.error(f"加载长期记忆失败: {e}")
    
    def _save_long_term_memory(self):
        """保存长期记忆"""
        try:
            # 按用户ID分组存储
            user_memories = {}
            for memory_id, memory in self.long_term_memory.items():
                user_id = memory.user_id
                if user_id not in user_memories:
                    user_memories[user_id] = {}
                user_memories[user_id][memory_id] = memory
            
            # 压缩存储
            for user_id, memories in user_memories.items():
                file_path = os.path.join(self.long_term_memory_dir, f"{user_id}.gz")
                with gzip.open(file_path, 'wb') as f:
                    pickle.dump(memories, f)
        except Exception as e:
            logger.error(f"保存长期记忆失败: {e}")
    
    def _schedule_cleanup(self):
        """调度定期清理任务"""
        # 这里可以使用APScheduler来定期执行清理任务
        # 为了简单起见，我们在每次操作时检查是否需要清理
        pass
    
    def _schedule_consolidation(self):
        """调度定期固化任务"""
        # 这里可以使用APScheduler来定期执行固化任务
        # 为了简单起见，我们在每次操作时检查是否需要固化
        pass
    
    def _active_forgetting(self):
        """主动遗忘模块"""
        try:
            logger.info("开始执行主动遗忘")
            
            # 遍历短期记忆
            if self.chroma_client:
                # ChromaDB的操作需要根据具体API调整
                pass
            else:
                # 从内存存储获取短期记忆
                to_delete = []
                for memory_id, memory in self.short_term_memory.items():
                    # 计算重要性衰减
                    days_since_creation = (time.time() - memory.timestamp) / (24 * 3600)
                    memory.importance = memory.importance * (0.5 ** (days_since_creation / 30))
                    
                    # 检查是否需要标记为待删除
                    days_since_last_access = (time.time() - memory.last_accessed) / (24 * 3600)
                    if memory.importance < 0.1 and days_since_last_access > 90:
                        if not memory.marked_for_deletion:
                            memory.marked_for_deletion = True
                            memory.deletion_buffer_start = time.time()
                            logger.info(f"记忆 {memory_id} 标记为待删除")
                    
                    # 检查缓冲期是否结束
                    if memory.marked_for_deletion:
                        buffer_days = (time.time() - memory.deletion_buffer_start) / (24 * 3600)
                        if buffer_days > 30:
                            to_delete.append(memory_id)
                            logger.info(f"记忆 {memory_id} 缓冲期结束，准备删除")
                
                # 删除缓冲期结束的记忆
                for memory_id in to_delete:
                    del self.short_term_memory[memory_id]
            
            # 遍历长期记忆
            to_delete = []
            for memory_id, memory in self.long_term_memory.items():
                # 计算重要性衰减
                days_since_creation = (time.time() - memory.timestamp) / (24 * 3600)
                memory.importance = memory.importance * (0.5 ** (days_since_creation / 30))
                
                # 检查是否需要标记为待删除
                days_since_last_access = (time.time() - memory.last_accessed) / (24 * 3600)
                if memory.importance < 0.1 and days_since_last_access > 90:
                    if not memory.marked_for_deletion:
                        memory.marked_for_deletion = True
                        memory.deletion_buffer_start = time.time()
                        logger.info(f"记忆 {memory_id} 标记为待删除")
                
                # 检查缓冲期是否结束
                if memory.marked_for_deletion:
                    buffer_days = (time.time() - memory.deletion_buffer_start) / (24 * 3600)
                    if buffer_days > 30:
                        to_delete.append(memory_id)
                        logger.info(f"记忆 {memory_id} 缓冲期结束，准备删除")
            
            # 删除缓冲期结束的记忆
            for memory_id in to_delete:
                del self.long_term_memory[memory_id]
            
            # 保存长期记忆
            self._save_long_term_memory()
            
            logger.info("主动遗忘执行完成")
        except Exception as e:
            logger.error(f"主动遗忘执行失败: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的嵌入向量"""
        try:
            if self.bert_model and self.tokenizer:
                # 使用BERT模型生成嵌入向量
                inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                # 使用[CLS] token的嵌入作为文本表示
                embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy().tolist()
                # 归一化
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = (np.array(embedding) / norm).tolist()
                return embedding
            else:
                # 回退到字符频率嵌入
                chars = set(text)
                embedding = []
                for c in 'abcdefghijklmnopqrstuvwxyz0123456789，。！？；："':
                    embedding.append(text.count(c) / len(text) if text else 0.0)
                # 归一化
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = (np.array(embedding) / norm).tolist()
                # 填充到768维
                while len(embedding) < 768:
                    embedding.append(0.0)
                return embedding[:768]  # 限制长度为768
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            # 出错时返回零向量
            return [0.0] * 768
    
    def _calculate_memory_value(self, memory: MemoryItem) -> float:
        """计算记忆的价值（基于访问频率和时间）"""
        # 基于艾宾浩斯遗忘曲线计算时间衰减因子
        time_since_creation = time.time() - memory.timestamp
        days_since_creation = time_since_creation / (24 * 3600)
        
        # 艾宾浩斯遗忘曲线公式：R(t) = e^(-t/S)，其中S是记忆强度
        memory_strength = 1.0
        forgetting_factor = np.exp(-days_since_creation / (memory_strength * 7))
        
        # 访问频率因子
        access_factor = min(1.0, memory.access_count / 10)
        
        # 综合价值
        return forgetting_factor * (1 + access_factor)
    
    def _calculate_memory_connection(self, memory1: MemoryItem, memory2: MemoryItem) -> float:
        """计算两个记忆之间的关联强度"""
        # 初始化关联强度
        connection_strength = 0.0
        
        # 1. 关键词重叠
        text1 = json.dumps(memory1.request) + " " + json.dumps(memory1.result)
        text2 = json.dumps(memory2.request) + " " + json.dumps(memory2.result)
        
        # 提取关键词（简单实现：使用空格分割的词）
        words1 = set(text1.split())
        words2 = set(text2.split())
        common_words = words1.intersection(words2)
        
        # 计算关键词重叠比例
        if words1 or words2:
            overlap_ratio = len(common_words) / (len(words1) + len(words2) - len(common_words))
            connection_strength += overlap_ratio * 0.5  # 关键词重叠权重0.5
        
        # 2. 时间邻近
        time_diff = abs(memory1.timestamp - memory2.timestamp)
        days_diff = time_diff / (24 * 3600)
        
        # 时间邻近度（越近强度越高）
        if days_diff < 7:  # 7天内的记忆认为是时间邻近的
            time_factor = max(0, 1 - days_diff / 7)
            connection_strength += time_factor * 0.3  # 时间邻近权重0.3
        
        # 3. 用户共同提及（如果是同一用户的记忆）
        if memory1.user_id == memory2.user_id:
            connection_strength += 0.2  # 同一用户权重0.2
        
        # 归一化到0-1范围
        return min(1.0, connection_strength)
    
    def _is_important_memory(self, memory: MemoryItem) -> bool:
        """判断记忆是否重要"""
        # 检查是否包含用户明确表达的偏好
        request_text = json.dumps(memory.request)
        result_text = json.dumps(memory.result)
        
        # 偏好关键词
        preference_keywords = ['喜欢', '偏好', '想要', '希望', '需求', '要求', '预算', '面积', '位置', '户型', '学区', '地铁']
        
        # 任务完成关键词
        task_keywords = ['完成', '成功', '已处理', '已完成', '解决', '搞定']
        
        # 检查是否包含重要关键词
        for keyword in preference_keywords:
            if keyword in request_text or keyword in result_text:
                return True
        
        for keyword in task_keywords:
            if keyword in result_text:
                return True
        
        # 检查访问频率
        if memory.access_count > 2:
            return True
        
        return False
    
    def _extract_memory_summary(self, memory: MemoryItem) -> str:
        """提取记忆摘要"""
        request_text = json.dumps(memory.request)
        result_text = json.dumps(memory.result)
        
        # 简单摘要生成
        if len(request_text) > 50:
            request_summary = request_text[:50] + "..."
        else:
            request_summary = request_text
        
        if len(result_text) > 50:
            result_summary = result_text[:50] + "..."
        else:
            result_summary = result_text
        
        return f"请求: {request_summary} 响应: {result_summary}"
    
    def _extract_memory_tags(self, memory: MemoryItem) -> List[str]:
        """提取记忆标签"""
        tags = []
        
        # 从请求中提取标签
        request_type = memory.request.get('type', 'unknown')
        tags.append(f"type:{request_type}")
        
        # 从中间数据中提取标签
        if 'intent' in memory.intermediate_data:
            intent = memory.intermediate_data['intent']
            tags.append(f"intent:{intent}")
        
        # 从结果中提取标签
        if 'status' in memory.result:
            status = memory.result['status']
            tags.append(f"status:{status}")
        
        return tags
    
    def _check_working_memory_threshold(self):
        """检查工作记忆是否达到阈值"""
        try:
            if self.redis_client:
                # 从Redis获取工作记忆数量
                keys = self.redis_client.keys("memory:*")
                return len(keys) >= self.working_memory_threshold
            else:
                # 从内存存储获取工作记忆数量
                return len(self.working_memory) >= self.working_memory_threshold
        except Exception as e:
            logger.error(f"检查工作记忆阈值失败: {e}")
            return False
    
    def _transfer_to_short_term_memory(self):
        """将工作记忆转换为短期记忆"""
        try:
            logger.info("开始工作记忆到短期记忆的转换")
            
            # 获取所有工作记忆
            working_memories = []
            
            if self.redis_client:
                # 从Redis获取所有工作记忆
                keys = self.redis_client.keys("memory:*")
                for key in keys:
                    data = self.redis_client.hgetall(key)
                    if data:
                        memory_item = MemoryItem(
                            memory_id=data["memory_id"],
                            user_id=data["user_id"],
                            request=json.loads(data["request"]),
                            intermediate_data=json.loads(data["intermediate_data"]),
                            result=json.loads(data["result"]),
                            timestamp=float(data["timestamp"]),
                            metadata=json.loads(data["metadata"])
                        )
                        working_memories.append(memory_item)
            else:
                # 从内存存储获取所有工作记忆
                working_memories = list(self.working_memory.values())
            
            # 筛选重要记忆
            important_memories = [m for m in working_memories if self._is_important_memory(m)]
            logger.info(f"筛选出 {len(important_memories)} 条重要记忆")
            
            # 转换为短期记忆
            for memory in important_memories:
                # 提取摘要和标签
                summary = self._extract_memory_summary(memory)
                tags = self._extract_memory_tags(memory)
                
                # 生成文本表示
                text_representation = json.dumps(memory.request) + " " + json.dumps(memory.result)
                
                # 生成嵌入向量
                embedding = self._get_embedding(text_representation)
                
                # 存储到短期记忆（ChromaDB）
                if self.chroma_client:
                    self.memory_collection.add(
                        ids=[memory.memory_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "user_id": memory.user_id,
                            "timestamp": memory.timestamp,
                            "request_type": memory.request.get("type", "unknown"),
                            "summary": summary,
                            "tags": json.dumps(tags),
                            "is_important": True
                        }],
                        documents=[text_representation]
                    )
                    logger.info(f"记忆 {memory.memory_id} 已转换到短期记忆")
                else:
                    # 使用内存存储
                    self.short_term_memory[memory.memory_id] = memory
            
            logger.info("工作记忆到短期记忆的转换完成")
        except Exception as e:
            logger.error(f"工作记忆到短期记忆的转换失败: {e}")
    
    def _consolidate_to_long_term_memory(self):
        """将短期记忆固化到长期记忆（Neo4j）"""
        try:
            logger.info("开始短期记忆到长期记忆的固化")
            
            # 获取所有短期记忆
            short_term_memories = []
            
            if self.chroma_client:
                # 从ChromaDB获取所有短期记忆
                # 注意：ChromaDB的API可能需要根据具体版本调整
                pass
            else:
                # 从内存存储获取所有短期记忆
                short_term_memories = list(self.short_term_memory.values())
            
            # 计算每个记忆的价值并筛选高价值记忆
            high_value_memories = []
            for memory in short_term_memories:
                value = self._calculate_memory_value(memory)
                if value > 0.5:  # 价值阈值
                    high_value_memories.append((memory, value))
            
            # 按价值排序
            high_value_memories.sort(key=lambda x: x[1], reverse=True)
            high_value_memories = [mem for mem, _ in high_value_memories]
            
            logger.info(f"筛选出 {len(high_value_memories)} 条高价值记忆")
            
            # 固化到长期记忆（Neo4j）
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    # 创建记忆节点
                    for memory in high_value_memories:
                        summary = self._extract_memory_summary(memory)
                        value = self._calculate_memory_value(memory)
                        tags = self._extract_memory_tags(memory)
                        
                        # 创建节点
                        session.run(
                            """
                            MERGE (m:Memory {memory_id: $memory_id})
                            SET m.user_id = $user_id,
                                m.summary = $summary,
                                m.importance = $importance,
                                m.timestamp = $timestamp,
                                m.request = $request,
                                m.result = $result,
                                m.tags = $tags
                            """,
                            memory_id=memory.memory_id,
                            user_id=memory.user_id,
                            summary=summary,
                            importance=value,
                            timestamp=memory.timestamp,
                            request=json.dumps(memory.request),
                            result=json.dumps(memory.result),
                            tags=json.dumps(tags)
                        )
                        logger.info(f"记忆 {memory.memory_id} 已固化到长期记忆（Neo4j）")
                    
                    # 为具有语义关联的记忆建立边
                    for i, memory1 in enumerate(high_value_memories):
                        for j, memory2 in enumerate(high_value_memories):
                            if i < j:  # 避免重复处理
                                connection_strength = self._calculate_memory_connection(memory1, memory2)
                                if connection_strength > 0.3:  # 关联强度阈值
                                    session.run(
                                        """
                                        MATCH (m1:Memory {memory_id: $memory_id1})
                                        MATCH (m2:Memory {memory_id: $memory_id2})
                                        MERGE (m1)-[r:RELATED_TO]->(m2)
                                        SET r.strength = $strength
                                        """,
                                        memory_id1=memory1.memory_id,
                                        memory_id2=memory2.memory_id,
                                        strength=connection_strength
                                    )
                                    logger.info(f"为记忆 {memory1.memory_id} 和 {memory2.memory_id} 建立关联，强度: {connection_strength}")
            else:
                # 使用压缩存储作为备份
                for memory in high_value_memories:
                    self.long_term_memory[memory.memory_id] = memory
                self._save_long_term_memory()
                logger.info("高价值记忆已固化到长期记忆（压缩存储）")
            
            logger.info("短期记忆到长期记忆的固化完成")
        except Exception as e:
            logger.error(f"短期记忆到长期记忆的固化失败: {e}")
    
    def _activate_related_memories(self):
        """从长期记忆（L3）反向激活短期记忆（L2）中的相关记忆"""
        try:
            logger.info("开始从长期记忆激活相关短期记忆")
            
            # 获取短期记忆
            if self.chroma_client:
                # ChromaDB的操作需要根据具体API调整
                pass
            else:
                short_term_memories = list(self.short_term_memory.values())
            
            # 获取长期记忆中的高重要性记忆
            high_importance_long_term_memories = []
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    # 查询高重要性记忆
                    result = session.run(
                        """
                        MATCH (m:Memory)
                        WHERE m.importance > 0.7
                        RETURN m.memory_id, m.importance
                        ORDER BY m.importance DESC
                        LIMIT 10
                        """
                    )
                    
                    for record in result:
                        memory_id = record["m.memory_id"]
                        memory = self.get_memory(memory_id)
                        if memory:
                            high_importance_long_term_memories.append(memory)
            else:
                # 从压缩存储获取高重要性记忆
                for memory_id, memory in self.long_term_memory.items():
                    if memory.importance > 0.7:
                        high_importance_long_term_memories.append(memory)
            
            logger.info(f"找到 {len(high_importance_long_term_memories)} 条高重要性长期记忆")
            
            # 激活相关的短期记忆
            activated_count = 0
            for long_term_memory in high_importance_long_term_memories:
                for short_term_memory in short_term_memories:
                    # 计算关联强度
                    connection_strength = self._calculate_memory_connection(long_term_memory, short_term_memory)
                    if connection_strength > 0.5:  # 关联强度阈值
                        # 提升短期记忆的重要性
                        short_term_memory.importance = min(1.0, short_term_memory.importance * 1.2)
                        # 更新最后访问时间
                        short_term_memory.last_accessed = time.time()
                        activated_count += 1
                        logger.info(f"激活短期记忆 {short_term_memory.memory_id}，关联强度: {connection_strength}")
            
            logger.info(f"成功激活 {activated_count} 条短期记忆")
            logger.info("从长期记忆激活相关短期记忆完成")
        except Exception as e:
            logger.error(f"从长期记忆激活相关短期记忆失败: {e}")

    def _calculate_retrieval_reward(self, node: RetrievalNode, path: RetrievalPath, query: Dict[str, Any]) -> float:
        """
        ReMemR1多级奖励计算
        基于命中、精确度、召回率、新颖性等多维度评估检索质量

        Args:
            node: 当前检索节点
            path: 检索路径
            query: 查询条件

        Returns:
            奖励信号值
        """
        reward = self._reward_config.hit_reward

        if node.similarity_score > 0.8:
            reward += self._reward_config.precision_bonus
        elif node.similarity_score > 0.5:
            reward += self._reward_config.precision_bonus * 0.5

        if node.revisited_count > 0:
            reward += self._reward_config.revisit_penalty * node.revisited_count

        if node.backtracked:
            reward += self._reward_config.backtrack_cost

        is_novel = True
        for existing_node in path.nodes:
            if existing_node.node_id != node.node_id and existing_node.memory.memory_id == node.memory.memory_id:
                is_novel = False
                break

        if is_novel and len(path.nodes) > 1:
            request_text = json.dumps(node.memory.request)
            query_text = json.dumps(query)
            words_request = set(request_text.split())
            words_query = set(query_text.split())
            unexpected_overlap = len(words_request & words_query) / max(len(words_query), 1)

            if 0.1 < unexpected_overlap < 0.5:
                reward += self._reward_config.serendipity_bonus
                self._retrieval_stats["novelty_discoveries"] += 1
            elif unexpected_overlap <= 0.1:
                reward += self._reward_config.novelty_bonus

        relevance_component = node.similarity_score * self._reward_config.relevance_weight
        reward = reward * 0.4 + relevance_component * 0.6

        return max(-1.0, min(2.0, reward))

    def _update_memory_on_retrieval(self, memory: MemoryItem, retrieval_reward: float):
        """
        ReMemR1检索集成记忆更新
        在检索过程中动态更新记忆的重要性评分

        Args:
            memory: 被检索的记忆项
            retrieval_reward: 该次检索的奖励信号
        """
        memory.access_count += 1
        memory.last_accessed = time.time()

        if retrieval_reward > 0.5:
            memory.importance = min(1.0, memory.importance + 0.05)
            logger.debug(f"记忆 {memory.memory_id} 因高奖励(+{retrieval_reward:.2f})提升重要性至 {memory.importance:.2f}")
        elif retrieval_reward < -0.3 and memory.importance > 0.15:
            memory.importance = max(0.1, memory.importance - 0.03)
            logger.debug(f"记忆 {memory.memory_id} 因低奖励({retrieval_reward:.2f})降低重要性至 {memory.importance:.2f}")

        if memory.marked_for_deletion and retrieval_reward > 0.7:
            memory.marked_for_deletion = False
            memory.deletion_buffer_start = 0.0
            memory.importance = min(1.0, memory.importance * 1.3)
            logger.info(f"ReMemR1回溯恢复: 记忆 {memory.memory_id} 因高价值检索被恢复")

    def _revisitable_retrieve(self, user_id: str, query: Dict[str, Any], top_k: int = 5) -> tuple:
        """
        ReMemR1可回溯非线性检索核心方法
        支持在检索过程中回溯到之前的节点，探索替代路径

        Args:
            user_id: 用户ID
            query: 查询条件
            top_k: 返回数量上限

        Returns:
            (最终结果列表, RetrievalPath对象)
        """
        path_id = f"path_{hashlib.md5(f'{user_id}_{time.time()}'.encode()).hexdigest()[:12]}"
        path = RetrievalPath(path_id=path_id, query=query)

        layer_results = {
            "working": [],
            "short_term": [],
            "long_term": [],
        }

        layer_results["working"] = self._retrieve_working_memory(user_id, query)
        layer_results["short_term"] = self._retrieve_short_term_memory(user_id, query, top_k)
        layer_results["long_term"] = self._retrieve_long_term_memory(user_id, query, top_k)

        all_candidates = []
        for layer_name, results in layer_results.items():
            for memory, score in results:
                node = RetrievalNode(
                    node_id=f"{path_id}_node_{len(all_candidates)}",
                    memory=memory,
                    source_layer=layer_name,
                    similarity_score=score,
                    retrieval_depth=0,
                )
                reward = self._calculate_retrieval_reward(node, path, query)
                node.reward_signal = reward
                path.add_node(node)
                all_candidates.append((node, score, reward))
                self._update_memory_on_retrieval(memory, reward)

        sorted_candidates = sorted(all_candidates, key=lambda x: (x[2], x[1]), reverse=True)
        final_nodes = sorted_candidates[:top_k]

        path.is_complete = True
        path.total_reward = sum(n.reward_signal for n, _, _ in final_nodes)
        self._retrieval_paths[path_id] = path

        backtrack_needed = False
        for node, _, reward in final_nodes:
            if reward < 0 and node.source_layer == "working":
                backtrack_needed = True
                break

        if backtrack_needed and path.backtrack_count < self._max_backtrack_depth:
            logger.info(f"ReMemR1触发回溯: path={path_id}, 当前奖励较低，探索替代路径")
            backtracked_node = path.backtrack()
            if backtracked_node:
                alt_source = "short_term" if backtracked_node.source_layer == "working" else "long_term"
                alt_results = layer_results.get(alt_source, [])
                if alt_results:
                    best_alt = alt_results[0]
                    alt_node = RetrievalNode(
                        node_id=f"{path_id}_alt_{path.backtrack_count}",
                        memory=best_alt[0],
                        source_layer=alt_source,
                        similarity_score=best_alt[1],
                        retrieval_depth=path.backtrack_count,
                        parent_node_id=backtracked_node.node_id,
                    )
                    alt_reward = self._calculate_retrieval_reward(alt_node, path, query)
                    alt_node.reward_signal = alt_reward
                    path.add_node(alt_node)
                    self._update_memory_on_retrieval(best_alt[0], alt_reward)

        self._retrieval_stats["total_retrievals"] += 1
        total_len = sum(len(r) for r in layer_results.values())
        self._retrieval_stats["avg_path_length"] = (
            (self._retrieval_stats["avg_path_length"] * (self._retrieval_stats["total_retrievals"] - 1) + len(path.nodes))
            / self._retrieval_stats["total_retrievals"]
        )
        if self._retrieval_stats["total_retrievals"] > 0:
            self._retrieval_stats["backtrack_rate"] = (
                self._retrieval_stats.get("backtrack_count", 0) / self._retrieval_stats["total_retrievals"]
            )
        self._retrieval_stats["avg_reward"] = (
            (self._retrieval_stats["avg_reward"] * (self._retrieval_stats["total_retrievals"] - 1) + path.total_reward)
            / self._retrieval_stats["total_retrievals"]
        )

        final_memories = [node.memory for node, _, _ in final_nodes]
        logger.info(f"ReMemR1检索完成: path={path_id}, nodes={len(path.nodes)}, backtracks={path.backtrack_count}, total_reward={path.total_reward:.2f}")

        return final_memories, path

    def _retrieve_working_memory(self, user_id: str, query: Dict[str, Any]) -> List[tuple]:
        """工作记忆层检索"""
        results = []
        try:
            if self.redis_client:
                keys = self.redis_client.keys("memory:*")
                for key in keys:
                    data = self.redis_client.hgetall(key)
                    if data.get("user_id") == user_id:
                        match = True
                        for qk, qv in query.items():
                            req_data = json.loads(data.get("request", "{}"))
                            if qk in req_data and req_data[qk] != qv:
                                match = False
                                break
                        if match:
                            mem = MemoryItem(
                                memory_id=data["memory_id"],
                                user_id=data["user_id"],
                                request=json.loads(data["request"]),
                                intermediate_data=json.loads(data["intermediate_data"]),
                                result=json.loads(data["result"]),
                                timestamp=float(data["timestamp"]),
                                metadata=json.loads(data.get("metadata", "{}")),
                            )
                            results.append((mem, 1.0))
            else:
                for memory in self.working_memory.values():
                    if memory.user_id == user_id:
                        match = True
                        for qk, qv in query.items():
                            if qk in memory.request and memory.request[qk] != qv:
                                match = False
                                break
                        if match:
                            results.append((memory, 1.0))
        except Exception as e:
            logger.error(f"工作记忆层检索失败: {e}")
        return results

    def _retrieve_short_term_memory(self, user_id: str, query: Dict[str, Any], top_k: int) -> List[tuple]:
        """短期记忆层检索"""
        results = []
        try:
            if self.chroma_client:
                query_text = json.dumps(query)
                query_embedding = self._get_embedding(query_text)
                search_results = self.memory_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where={"user_id": user_id}
                )
                for i, (mid, dist) in enumerate(zip(search_results["ids"][0], search_results["distances"][0])):
                    mem = self.get_memory(mid)
                    if mem:
                        results.append((mem, max(0, 1 - dist)))
            else:
                all_mems = self.get_user_memories(user_id)
                for mem in all_mems:
                    t1, t2 = json.dumps(query), json.dumps(mem.request) + " " + json.dumps(mem.result)
                    w1, w2 = set(t1.split()), set(t2.split())
                    common = w1 & w2
                    if w1 or w2:
                        sim = len(common) / (len(w1) + len(w2) - len(common))
                        if sim > 0.1:
                            results.append((mem, sim))
        except Exception as e:
            logger.error(f"短期记忆层检索失败: {e}")
        return results

    def _retrieve_long_term_memory(self, user_id: str, query: Dict[str, Any], top_k: int) -> List[tuple]:
        """长期记忆层检索"""
        results = []
        try:
            query_text = json.dumps(query)
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    result = session.run(
                        """MATCH (m:Memory {user_id: $uid})
                        WHERE m.summary CONTAINS $qt OR m.request CONTAINS $qt OR m.result CONTAINS $qt
                        RETURN m.memory_id, m.importance ORDER BY m.importance DESC LIMIT $limit""",
                        uid=user_id, qt=query_text, limit=top_k
                    )
                    for record in result:
                        mid = record["m.memory_id"]
                        mem = self.get_memory(mid)
                        if mem:
                            results.append((mem, record["m.importance"]))
            else:
                for mid, mem in self.long_term_memory.items():
                    if mem.user_id == user_id:
                        t1, t2 = json.dumps(query), json.dumps(mem.request) + " " + json.dumps(mem.result)
                        w1, w2 = set(t1.split()), set(t2.split())
                        common = w1 & w2
                        if w1 or w2:
                            sim = len(common) / (len(w1) + len(w2) - len(common))
                            if sim > 0.1:
                                results.append((mem, sim))
        except Exception as e:
            logger.error(f"长期记忆层检索失败: {e}")
        return results

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取ReMemR1检索统计"""
        return {
            **self._retrieval_stats,
            "active_paths": len(self._retrieval_paths),
            "max_backtrack_depth": self._max_backtrack_depth,
        }
    
    def _cleanup_old_memories(self):
        """清理低价值记忆"""
        try:
            # 清理工作记忆（超过24小时的）
            if self.redis_client:
                keys = self.redis_client.keys("memory:*")
                for key in keys:
                    timestamp = float(self.redis_client.hget(key, "timestamp"))
                    if time.time() - timestamp > 24 * 3600:
                        self.redis_client.delete(key)
            else:
                # 使用内存存储时的清理
                to_delete = []
                for key, memory in self.working_memory.items():
                    if time.time() - memory.timestamp > 24 * 3600:
                        to_delete.append(key)
                for key in to_delete:
                    del self.working_memory[key]
            
            # 清理短期记忆（超过30天的）
            if self.chroma_client:
                # ChromaDB的清理需要根据具体API调整
                pass
            else:
                # 使用内存存储时的清理
                to_delete = []
                for memory_id, memory in self.short_term_memory.items():
                    if time.time() - memory.timestamp > 30 * 24 * 3600:
                        to_delete.append(memory_id)
                for memory_id in to_delete:
                    del self.short_term_memory[memory_id]
            
            # 清理长期记忆中的低价值记忆
            low_value_memories = []
            for memory_id, memory in self.long_term_memory.items():
                value = self._calculate_memory_value(memory)
                if value < 0.1:  # 价值阈值
                    low_value_memories.append(memory_id)
            
            for memory_id in low_value_memories:
                del self.long_term_memory[memory_id]
            
            # 保存长期记忆
            self._save_long_term_memory()
            
            logger.info("记忆清理完成")
        except Exception as e:
            logger.error(f"记忆清理失败: {e}")
    
    def create_memory(self, user_id: str, request: Dict[str, Any], intermediate_data: Dict[str, Any], result: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """创建新的记忆"""
        # 生成记忆ID
        memory_id = hashlib.md5(f"{user_id}_{time.time()}_{json.dumps(request)}".encode()).hexdigest()
        
        # 创建记忆项
        memory_item = MemoryItem(
            memory_id=memory_id,
            user_id=user_id,
            request=request,
            intermediate_data=intermediate_data,
            result=result,
            timestamp=time.time(),
            metadata=metadata or {},
            importance=1.0,  # 初始重要性
            marked_for_deletion=False,  # 初始未标记为待删除
            deletion_buffer_start=0.0  # 初始缓冲期开始时间为0
        )
        
        # 存储到工作记忆（Redis）
        if self.redis_client:
            key = f"memory:{memory_id}"
            self.redis_client.hset(key, mapping={
                "memory_id": memory_id,
                "user_id": user_id,
                "request": json.dumps(request),
                "intermediate_data": json.dumps(intermediate_data),
                "result": json.dumps(result),
                "timestamp": str(time.time()),
                "metadata": json.dumps(metadata or {})
            })
            # 设置24小时过期
            self.redis_client.expire(key, 24 * 3600)
        else:
            self.working_memory[memory_id] = memory_item
        
        # 存储到短期记忆（ChromaDB）
        if self.chroma_client:
            # 生成嵌入向量
            text_representation = json.dumps(request) + " " + json.dumps(result)
            embedding = self._get_embedding(text_representation)
            
            # 存储到ChromaDB
            self.memory_collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": user_id,
                    "timestamp": time.time(),
                    "request_type": request.get("type", "unknown")
                }],
                documents=[text_representation]
            )
        else:
            self.short_term_memory[memory_id] = memory_item
        
        # 存储到长期记忆（压缩存储）
        self.long_term_memory[memory_id] = memory_item
        
        # 更新用户画像
        self.update_user_profile(user_id, memory_id, request, result)
        
        # 检查是否需要清理
        if len(self.long_term_memory) % 10 == 0:
            self._cleanup_old_memories()
        
        # 检查工作记忆是否达到阈值，如果达到则触发转换
        if self._check_working_memory_threshold():
            self._transfer_to_short_term_memory()
        
        return memory_id
    
    def update_user_profile(self, user_id: str, memory_id: str, request: Dict[str, Any], result: Dict[str, Any]):
        """更新用户画像"""
        # 这里可以实现用户画像的存储和更新
        # 为了简单起见，我们暂时使用内存存储
        pass
    
    def _update_preferences(self, profile: UserProfile, request: Dict[str, Any], result: Dict[str, Any]):
        """更新用户偏好"""
        # 从请求中提取偏好信息
        if "property_type" in request:
            profile.preferences["property_type"] = request["property_type"]
        
        if "area" in request:
            profile.preferences["area"] = request["area"]
        
        if "budget" in request:
            profile.preferences["budget"] = request["budget"]
        
        # 从结果中提取偏好信息
        if "valuation" in result:
            profile.preferences["last_valuation"] = result["valuation"]
        
        if "preferred_features" in result:
            profile.preferences["preferred_features"] = result["preferred_features"]
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        # 首先从工作记忆中查找
        if self.redis_client:
            key = f"memory:{memory_id}"
            if self.redis_client.exists(key):
                data = self.redis_client.hgetall(key)
                memory_item = MemoryItem(
                    memory_id=data["memory_id"],
                    user_id=data["user_id"],
                    request=json.loads(data["request"]),
                    intermediate_data=json.loads(data["intermediate_data"]),
                    result=json.loads(data["result"]),
                    timestamp=float(data["timestamp"]),
                    metadata=json.loads(data["metadata"])
                )
                # 更新访问计数
                memory_item.access_count += 1
                memory_item.last_accessed = time.time()
                return memory_item
        else:
            if memory_id in self.working_memory:
                memory_item = self.working_memory[memory_id]
                memory_item.access_count += 1
                memory_item.last_accessed = time.time()
                return memory_item
        
        # 从短期记忆中查找
        if self.chroma_client:
            # ChromaDB的查询需要根据具体API调整
            pass
        else:
            if memory_id in self.short_term_memory:
                memory_item = self.short_term_memory[memory_id]
                # 更新访问计数
                memory_item.access_count += 1
                memory_item.last_accessed = time.time()
                # 如果记忆在缓冲期内被访问，恢复并提升重要性
                if memory_item.marked_for_deletion:
                    memory_item.marked_for_deletion = False
                    memory_item.deletion_buffer_start = 0.0
                    memory_item.importance = min(1.0, memory_item.importance * 1.5)  # 提升重要性
                    logger.info(f"记忆 {memory_id} 在缓冲期内被访问，已恢复并提升重要性")
                return memory_item
        
        # 从长期记忆中查找
        if memory_id in self.long_term_memory:
            memory_item = self.long_term_memory[memory_id]
            # 更新访问计数
            memory_item.access_count += 1
            memory_item.last_accessed = time.time()
            # 如果记忆在缓冲期内被访问，恢复并提升重要性
            if memory_item.marked_for_deletion:
                memory_item.marked_for_deletion = False
                memory_item.deletion_buffer_start = 0.0
                memory_item.importance = min(1.0, memory_item.importance * 1.5)  # 提升重要性
                logger.info(f"记忆 {memory_id} 在缓冲期内被访问，已恢复并提升重要性")
            return memory_item
        
        return None
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        # 这里可以实现用户画像的获取
        # 为了简单起见，我们暂时返回None
        return None
    
    def get_user_memories(self, user_id: str) -> List[MemoryItem]:
        """获取用户的所有记忆"""
        memories = []
        
        # 从工作记忆中获取
        if self.redis_client:
            keys = self.redis_client.keys("memory:*")
            for key in keys:
                data = self.redis_client.hgetall(key)
                if data.get("user_id") == user_id:
                    memory_item = MemoryItem(
                        memory_id=data["memory_id"],
                        user_id=data["user_id"],
                        request=json.loads(data["request"]),
                        intermediate_data=json.loads(data["intermediate_data"]),
                        result=json.loads(data["result"]),
                        timestamp=float(data["timestamp"]),
                        metadata=json.loads(data["metadata"])
                    )
                    memories.append(memory_item)
        else:
            for memory in self.working_memory.values():
                if memory.user_id == user_id:
                    memories.append(memory)
        
        # 从短期记忆中获取
        if self.chroma_client:
            # ChromaDB的查询需要根据具体API调整
            pass
        else:
            for memory in self.short_term_memory.values():
                if memory.user_id == user_id:
                    memories.append(memory)
        
        # 从长期记忆中获取
        for memory in self.long_term_memory.values():
            if memory.user_id == user_id:
                memories.append(memory)
        
        # 按时间排序
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        return memories
    
    def search_memories(self, user_id: str, query: Dict[str, Any], top_k: int = 5) -> List[MemoryItem]:
        """搜索记忆"""
        results = []
        seen_memory_ids = set()
        
        # 使用ChromaDB进行相似度搜索
        if self.chroma_client:
            # 生成查询向量
            query_text = json.dumps(query)
            query_embedding = self._get_embedding(query_text)
            
            # 搜索
            search_results = self.memory_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"user_id": user_id}
            )
            
            # 处理结果
            for i, memory_id in enumerate(search_results["ids"][0]):
                if memory_id not in seen_memory_ids:
                    seen_memory_ids.add(memory_id)
                    memory = self.get_memory(memory_id)
                    if memory:
                        results.append(memory)
        else:
            # 使用简单的匹配逻辑
            all_memories = self.get_user_memories(user_id)
            for memory in all_memories:
                if memory.memory_id not in seen_memory_ids:
                    match = True
                    for key, value in query.items():
                        if key in memory.request and memory.request[key] != value:
                            match = False
                            break
                        if key in memory.result and memory.result[key] != value:
                            match = False
                            break
                    if match:
                        seen_memory_ids.add(memory.memory_id)
                        results.append(memory)
                    if len(results) >= top_k:
                        break
        
        return results
    
    def delete_memory(self, memory_id: str):
        """删除记忆"""
        # 从工作记忆中删除
        if self.redis_client:
            key = f"memory:{memory_id}"
            self.redis_client.delete(key)
        else:
            if memory_id in self.working_memory:
                del self.working_memory[memory_id]
        
        # 从短期记忆中删除
        if self.chroma_client:
            self.memory_collection.delete(ids=[memory_id])
        else:
            if memory_id in self.short_term_memory:
                del self.short_term_memory[memory_id]
        
        # 从长期记忆中删除
        if memory_id in self.long_term_memory:
            del self.long_term_memory[memory_id]
            self._save_long_term_memory()
    
    def clear_user_memories(self, user_id: str):
        """清除用户的所有记忆"""
        # 收集用户的所有记忆ID
        user_memory_ids = []
        
        # 从工作记忆中收集
        if self.redis_client:
            keys = self.redis_client.keys("memory:*")
            for key in keys:
                data = self.redis_client.hgetall(key)
                if data.get("user_id") == user_id:
                    user_memory_ids.append(data["memory_id"])
                    self.redis_client.delete(key)
        else:
            to_delete = []
            for memory_id, memory in self.working_memory.items():
                if memory.user_id == user_id:
                    to_delete.append(memory_id)
            for memory_id in to_delete:
                del self.working_memory[memory_id]
        
        # 从短期记忆中收集和删除
        if self.chroma_client:
            # ChromaDB的删除需要根据具体API调整
            pass
        else:
            to_delete = []
            for memory_id, memory in self.short_term_memory.items():
                if memory.user_id == user_id:
                    to_delete.append(memory_id)
            for memory_id in to_delete:
                del self.short_term_memory[memory_id]
        
        # 从长期记忆中收集和删除
        to_delete = []
        for memory_id, memory in self.long_term_memory.items():
            if memory.user_id == user_id:
                to_delete.append(memory_id)
        for memory_id in to_delete:
            del self.long_term_memory[memory_id]
        
        # 保存长期记忆
        self._save_long_term_memory()
    
    def retrieve_memories(self, user_id: str, query: Dict[str, Any], top_k: int = 5) -> List[MemoryItem]:
        """
        检索记忆（三层检索并融合）- ReMemR1可回溯增强版
        支持非线性回溯检索与多级奖励驱动的记忆更新
        """
        try:
            logger.info(f"开始ReMemR1增强检索记忆，用户ID: {user_id}")

            final_results, retrieval_path = self._revisitable_retrieve(user_id, query, top_k)

            logger.info(f"最终检索结果: {len(final_results)} 条 (ReMemR1 path={retrieval_path.path_id})")
            return final_results

        except Exception as e:
            logger.error(f"ReMemR1增强检索失败，回退到基础检索: {e}")
            return self._fallback_retrieve(user_id, query, top_k)

    def _fallback_retrieve(self, user_id: str, query: Dict[str, Any], top_k: int = 5) -> List[MemoryItem]:
        """回退到基础三层检索（当ReMemR1不可用时）"""
        try:
            working_memory_results = []
            seen_memory_ids = set()

            if self.redis_client:
                keys = self.redis_client.keys("memory:*")
                for key in keys:
                    data = self.redis_client.hgetall(key)
                    if data.get("user_id") == user_id:
                        match = True
                        for key, value in query.items():
                            request_data = json.loads(data["request"])
                            if key in request_data and request_data[key] != value:
                                match = False
                                break
                        if match:
                            memory_item = MemoryItem(
                                memory_id=data["memory_id"],
                                user_id=data["user_id"],
                                request=json.loads(data["request"]),
                                intermediate_data=json.loads(data["intermediate_data"]),
                                result=json.loads(data["result"]),
                                timestamp=float(data["timestamp"]),
                                metadata=json.loads(data["metadata"])
                            )
                            working_memory_results.append((memory_item, 1.0))
                            seen_memory_ids.add(memory_item.memory_id)
            else:
                for memory in self.working_memory.values():
                    if memory.user_id == user_id:
                        match = True
                        for key, value in query.items():
                            if key in memory.request and memory.request[key] != value:
                                match = False
                                break
                        if match:
                            working_memory_results.append((memory, 1.0))
                            seen_memory_ids.add(memory.memory_id)

            short_term_memory_results = []

            if self.chroma_client:
                query_text = json.dumps(query)
                query_embedding = self._get_embedding(query_text)
                search_results = self.memory_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where={"user_id": user_id}
                )
                for i, (memory_id, distance) in enumerate(zip(search_results["ids"][0], search_results["distances"][0])):
                    if memory_id not in seen_memory_ids:
                        seen_memory_ids.add(memory_id)
                        memory = self.get_memory(memory_id)
                        if memory:
                            similarity = max(0, 1 - distance)
                            short_term_memory_results.append((memory, similarity))
            else:
                all_memories = self.get_user_memories(user_id)
                for memory in all_memories:
                    if memory.memory_id not in seen_memory_ids:
                        text1 = json.dumps(query)
                        text2 = json.dumps(memory.request) + " " + json.dumps(memory.result)
                        words1 = set(text1.split())
                        words2 = set(text2.split())
                        common_words = words1.intersection(words2)
                        if words1 or words2:
                            similarity = len(common_words) / (len(words1) + len(words2) - len(common_words))
                            if similarity > 0.1:
                                short_term_memory_results.append((memory, similarity))
                                seen_memory_ids.add(memory.memory_id)

            short_term_memory_results.sort(key=lambda x: x[1], reverse=True)
            short_term_memory_results = short_term_memory_results[:top_k]

            long_term_memory_results = []

            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    query_text = json.dumps(query)
                    result = session.run(
                        """MATCH (m:Memory {user_id: $uid})
                        WHERE m.summary CONTAINS $qt OR m.request CONTAINS $qt OR m.result CONTAINS $qt
                        RETURN m.memory_id, m.importance ORDER BY m.importance DESC LIMIT $limit""",
                        uid=user_id, qt=query_text, limit=top_k
                    )
                    direct_memory_ids = []
                    for record in result:
                        memory_id = record["m.memory_id"]
                        if memory_id not in seen_memory_ids:
                            direct_memory_ids.append(memory_id)
                            seen_memory_ids.add(memory_id)
                            memory = self.get_memory(memory_id)
                            if memory:
                                long_term_memory_results.append((memory, record["m.importance"]))
                    for memory_id in direct_memory_ids:
                        result = session.run(
                            """MATCH (m1:Memory {memory_id: $mid})-[r:RELATED_TO]->(m2:Memory {user_id: $uid})
                            RETURN m2.memory_id, r.strength ORDER BY r.strength DESC LIMIT $limit""",
                            mid=memory_id, uid=user_id, limit=top_k
                        )
                        for record in result:
                            related_id = record["m2.memory_id"]
                            if related_id not in seen_memory_ids:
                                seen_memory_ids.add(related_id)
                                memory = self.get_memory(related_id)
                                if memory:
                                    long_term_memory_results.append((memory, record["r.strength"]))
            else:
                for memory_id, memory in self.long_term_memory.items():
                    if memory.user_id == user_id and memory_id not in seen_memory_ids:
                        text1 = json.dumps(query)
                        text2 = json.dumps(memory.request) + " " + json.dumps(memory.result)
                        words1 = set(text1.split())
                        words2 = set(text2.split())
                        common_words = words1.intersection(words2)
                        if words1 or words2:
                            similarity = len(common_words) / (len(words1) + len(words2) - len(common_words))
                            if similarity > 0.1:
                                long_term_memory_results.append((memory, similarity))
                                seen_memory_ids.add(memory_id)

            long_term_memory_results.sort(key=lambda x: x[1], reverse=True)
            long_term_memory_results = long_term_memory_results[:top_k]

            weights = {"working": 0.5, "short_term": 0.3, "long_term": 0.2}
            fused_results = []

            for memory, score in working_memory_results:
                fused_results.append((memory, score * weights["working"]))
            for memory, score in short_term_memory_results:
                fused_results.append((memory, score * weights["short_term"]))
            for memory, score in long_term_memory_results:
                fused_results.append((memory, score * weights["long_term"]))

            fused_results.sort(key=lambda x: x[1], reverse=True)
            fused_results = fused_results[:top_k]
            final_results = [memory for memory, _ in fused_results]

            logger.info(f"基础回退检索结果: {len(final_results)} 条")
            return final_results

        except Exception as e:
            logger.error(f"基础回退检索失败: {e}")
            return []


# 示例使用
if __name__ == "__main__":
    # 创建海马体实例
    hippocampus = Hippocampus()
    
    # 模拟用户请求
    user_id = "user_123"
    request = {
        "type": "valuation",
        "property_data": {
            "building_age": 10,
            "distance_to_subway": 500,
            "school_district_level": "A",
            "greening_rate": 35,
            "price_per_sqm": 85000,
            "total_area": 120,
            "room_count": 3,
            "bathroom_count": 2,
            "floor": 15,
            "total_floors": 30,
            "is_elevator": True,
            "property_type": "apartment"
        },
        "timestamp": time.time()
    }
    
    # 模拟中间数据
    intermediate_data = {
        "extracted_features": {
            "building_age": 0.3333,
            "distance_to_subway": 0.3,
            "school_district_level": 0.0,
            "greening_rate": 0.5,
            "price_per_sqm": 0.3636,
            "total_area": 0.3333,
            "room_count": 0.5,
            "bathroom_count": 0.5,
            "floor": 0.5,
            "total_floors": 0.6667,
            "is_elevator": 1.0,
            "property_type": 0.0
        },
        "valuation_steps": {
            "location": 60000.00,
            "layout": 66000.00,
            "market": 55290.00,
            "collaborative": 60319.47
        }
    }
    
    # 模拟结果
    result = {
        "valuation": 60319.47,
        "currency": "CNY",
        "unit": "元/㎡",
        "confidence": 0.85,
        "breakdown": {
            "location": 60000.00,
            "layout": 66000.00,
            "market": 55290.00
        },
        "recommendation": "该房产估值合理，建议进一步考察周边环境和市场趋势。"
    }
    
    # 创建记忆
    memory_id = hippocampus.create_memory(user_id, request, intermediate_data, result)
    print(f"创建记忆成功，记忆ID: {memory_id}")
    
    # 获取记忆
    retrieved_memory = hippocampus.get_memory(memory_id)
    print(f"检索记忆成功: {retrieved_memory.memory_id}")
    
    # 获取用户的所有记忆
    user_memories = hippocampus.get_user_memories(user_id)
    print(f"用户记忆数量: {len(user_memories)}")
    
    # 搜索记忆
    search_results = hippocampus.search_memories(user_id, {"type": "valuation"})
    print(f"搜索结果数量: {len(search_results)}")
    
    # 清理记忆
    hippocampus.delete_memory(memory_id)
    print(f"删除记忆成功")
    
    # 验证删除
    deleted_memory = hippocampus.get_memory(memory_id)
    print(f"记忆是否已删除: {deleted_memory is None}")
