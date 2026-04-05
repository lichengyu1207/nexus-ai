"""
思维原子库管理模块
存储和管理思维原子，支持向量检索
"""

import os
import json
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

# 延迟导入可能不兼容的库
chromadb = None

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    logger.warning(f"ChromaDB导入失败: {e}")

from backend.agents.atomic_extractor import ThoughtAtom


class AtomicLibrary:
    """思维原子库"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "atomic_library"
        )
        self.metadata_path = os.path.join(self.db_path, "metadata")
        self.vector_db = self._initialize_vector_db()
        self.collection = None
        self._initialize_collection()
        self._load_metadata()
    
    def _initialize_vector_db(self):
        """初始化向量数据库"""
        if chromadb:
            try:
                os.makedirs(self.db_path, exist_ok=True)
                vector_db = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        persist_directory=self.db_path
                    )
                )
                logger.info("ChromaDB初始化成功")
                return vector_db
            except Exception as e:
                logger.error(f"初始化ChromaDB失败: {e}")
                return None
        else:
            logger.warning("ChromaDB不可用，使用内存存储")
            return None
    
    def _initialize_collection(self):
        """初始化向量集合"""
        if self.vector_db:
            try:
                # 创建或获取集合
                self.collection = self.vector_db.get_or_create_collection(
                    name="thought_atoms",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("向量集合初始化成功")
            except Exception as e:
                logger.error(f"初始化向量集合失败: {e}")
        else:
            # 使用内存存储
            self.memory_store = {
                "embeddings": [],
                "metadatas": [],
                "documents": [],
                "ids": []
            }
    
    def _load_metadata(self):
        """加载元数据"""
        os.makedirs(self.metadata_path, exist_ok=True)
        self.metadata = {}
        
        # 加载所有元数据文件
        for filename in os.listdir(self.metadata_path):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.metadata_path, filename), "r", encoding="utf-8") as f:
                        atom_data = json.load(f)
                        atom_id = filename.replace(".json", "")
                        self.metadata[atom_id] = atom_data
                except Exception as e:
                    logger.error(f"加载元数据文件 {filename} 失败: {e}")
    
    def add_atom(self, atom: ThoughtAtom) -> str:
        """添加思维原子
        
        Args:
            atom: 思维原子
            
        Returns:
            原子ID
        """
        try:
            # 生成原子ID
            atom_id = f"atom_{int(time.time() * 1000)}"
            
            # 准备向量数据
            embedding = atom.vector or self._generate_default_vector(atom)
            metadata = asdict(atom)
            metadata.pop("vector", None)  # 从元数据中移除向量
            document = f"{atom.name}: {atom.description}"
            
            # 存储到向量数据库
            if self.collection:
                self.collection.add(
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[document],
                    ids=[atom_id]
                )
            else:
                # 存储到内存
                self.memory_store["embeddings"].append(embedding)
                self.memory_store["metadatas"].append(metadata)
                self.memory_store["documents"].append(document)
                self.memory_store["ids"].append(atom_id)
            
            # 存储元数据
            metadata_file = os.path.join(self.metadata_path, f"{atom_id}.json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的元数据
            self.metadata[atom_id] = metadata
            
            logger.info(f"添加思维原子成功: {atom.name} (ID: {atom_id})")
            return atom_id
        except Exception as e:
            logger.error(f"添加思维原子失败: {e}")
            return None
    
    def add_atoms(self, atoms: List[ThoughtAtom]) -> List[str]:
        """批量添加思维原子
        
        Args:
            atoms: 思维原子列表
            
        Returns:
            原子ID列表
        """
        atom_ids = []
        for atom in atoms:
            atom_id = self.add_atom(atom)
            if atom_id:
                atom_ids.append(atom_id)
        return atom_ids
    
    def search_atoms(self, query: str, top_k: int = 5, scenario: Optional[str] = None) -> List[Tuple[ThoughtAtom, float]]:
        """搜索思维原子
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            scenario: 场景过滤
            
        Returns:
            思维原子和相似度列表
        """
        try:
            # 生成查询向量
            query_vector = self._generate_query_vector(query)
            
            # 搜索向量数据库
            if self.collection:
                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k,
                    where={"scenario": {"$contains": scenario}} if scenario else None
                )
                
                # 处理结果
                atoms_with_score = []
                for i, (id_, score, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["metadatas"][0]
                )):
                    # 计算相似度 (1 - 距离)
                    similarity = 1.0 - score
                    # 重建思维原子
                    atom = ThoughtAtom(
                        name=metadata.get("name"),
                        description=metadata.get("description"),
                        keywords=metadata.get("keywords", []),
                        scenario=metadata.get("scenario", []),
                        weight=metadata.get("weight", 0.5),
                        metadata=metadata
                    )
                    atoms_with_score.append((atom, similarity))
                
                # 按相似度排序
                atoms_with_score.sort(key=lambda x: x[1], reverse=True)
                return atoms_with_score
            else:
                # 使用内存搜索
                return self._search_in_memory(query_vector, top_k, scenario)
        except Exception as e:
            logger.error(f"搜索思维原子失败: {e}")
            return []
    
    def _search_in_memory(self, query_vector: List[float], top_k: int, scenario: Optional[str]) -> List[Tuple[ThoughtAtom, float]]:
        """在内存中搜索思维原子"""
        if not hasattr(self, "memory_store"):
            return []
        
        # 计算余弦相似度
        similarities = []
        for i, embedding in enumerate(self.memory_store["embeddings"]):
            similarity = self._cosine_similarity(query_vector, embedding)
            metadata = self.memory_store["metadatas"][i]
            
            # 场景过滤
            if scenario and scenario not in metadata.get("scenario", []):
                continue
            
            # 重建思维原子
            atom = ThoughtAtom(
                name=metadata.get("name"),
                description=metadata.get("description"),
                keywords=metadata.get("keywords", []),
                scenario=metadata.get("scenario", []),
                weight=metadata.get("weight", 0.5),
                metadata=metadata
            )
            similarities.append((atom, similarity))
        
        # 按相似度排序并返回前top_k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def update_atom_weight(self, atom_id: str, weight: float):
        """更新思维原子权重
        
        Args:
            atom_id: 原子ID
            weight: 新权重
        """
        try:
            # 更新元数据
            if atom_id in self.metadata:
                self.metadata[atom_id]["weight"] = weight
                
                # 保存到文件
                metadata_file = os.path.join(self.metadata_path, f"{atom_id}.json")
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(self.metadata[atom_id], f, ensure_ascii=False, indent=2)
                
                # 更新向量数据库
                if self.collection:
                    # 注意：ChromaDB不支持直接更新，需要删除后重新添加
                    # 这里简化处理，只更新元数据
                    pass
                
                logger.info(f"更新思维原子权重成功: {atom_id}, 新权重: {weight}")
        except Exception as e:
            logger.error(f"更新思维原子权重失败: {e}")
    
    def get_atom(self, atom_id: str) -> Optional[ThoughtAtom]:
        """获取思维原子
        
        Args:
            atom_id: 原子ID
            
        Returns:
            思维原子
        """
        try:
            if atom_id in self.metadata:
                metadata = self.metadata[atom_id]
                return ThoughtAtom(
                    name=metadata.get("name"),
                    description=metadata.get("description"),
                    keywords=metadata.get("keywords", []),
                    scenario=metadata.get("scenario", []),
                    weight=metadata.get("weight", 0.5),
                    metadata=metadata
                )
            return None
        except Exception as e:
            logger.error(f"获取思维原子失败: {e}")
            return None
    
    def get_all_atoms(self) -> List[ThoughtAtom]:
        """获取所有思维原子
        
        Returns:
            思维原子列表
        """
        atoms = []
        for atom_id, metadata in self.metadata.items():
            atom = ThoughtAtom(
                name=metadata.get("name"),
                description=metadata.get("description"),
                keywords=metadata.get("keywords", []),
                scenario=metadata.get("scenario", []),
                weight=metadata.get("weight", 0.5),
                metadata=metadata
            )
            atoms.append(atom)
        return atoms
    
    def _generate_query_vector(self, query: str) -> List[float]:
        """生成查询向量"""
        # 简单的基于规则的向量生成
        # 实际项目中应该使用与原子向量相同的模型
        vector = [0.0] * 768
        
        # 基于查询关键词生成向量
        keywords = query.split()
        for i, keyword in enumerate(keywords):
            if i < 768:
                # 简单的哈希值作为权重
                vector[i] = hash(keyword) % 10 / 10.0
        
        return vector
    
    def _generate_default_vector(self, atom: ThoughtAtom) -> List[float]:
        """生成默认向量"""
        # 基于规则生成向量
        vector = [0.0] * 768
        
        # 基于关键词生成向量
        for i, keyword in enumerate(atom.keywords):
            if i < 768:
                vector[i] = hash(keyword) % 10 / 10.0 * atom.weight
        
        # 基于场景生成向量
        for i, scene in enumerate(atom.scenario):
            if i + len(atom.keywords) < 768:
                vector[i + len(atom.keywords)] = 0.5 * atom.weight
        
        return vector
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            if norm1 * norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0


# 全局原子库实例
atomic_library: Optional[AtomicLibrary] = None


def get_atomic_library() -> AtomicLibrary:
    """获取原子库实例"""
    global atomic_library
    if atomic_library is None:
        atomic_library = AtomicLibrary()
    return atomic_library


def add_atom(atom: ThoughtAtom) -> str:
    """添加思维原子"""
    library = get_atomic_library()
    return library.add_atom(atom)


def add_atoms(atoms: List[ThoughtAtom]) -> List[str]:
    """批量添加思维原子"""
    library = get_atomic_library()
    return library.add_atoms(atoms)


def search_atoms(query: str, top_k: int = 5, scenario: Optional[str] = None) -> List[Tuple[ThoughtAtom, float]]:
    """搜索思维原子"""
    library = get_atomic_library()
    return library.search_atoms(query, top_k, scenario)


def update_atom_weight(atom_id: str, weight: float):
    """更新思维原子权重"""
    library = get_atomic_library()
    library.update_atom_weight(atom_id, weight)


def get_atom(atom_id: str) -> Optional[ThoughtAtom]:
    """获取思维原子"""
    library = get_atomic_library()
    return library.get_atom(atom_id)


def get_all_atoms() -> List[ThoughtAtom]:
    """获取所有思维原子"""
    library = get_atomic_library()
    return library.get_all_atoms()
