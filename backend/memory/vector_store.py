"""
智能体记忆系统 - 向量存储层
封装ChromaDB操作，支持语义检索
注意: chromadb 在 Python 3.14+ 可能不兼容，会自动降级为禁用向量搜索
"""
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

CHROMADB_AVAILABLE = False
EMBEDDINGS_AVAILABLE = False

if sys.version_info < (3, 14):
    try:
        import chromadb
        from chromadb.config import Settings
        CHROMADB_AVAILABLE = True
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: chromadb initialization failed: {e}")

    try:
        from sentence_transformers import SentenceTransformer
        EMBEDDINGS_AVAILABLE = True
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: sentence_transformers initialization failed: {e}")
else:
    print("Warning: Python 3.14+ detected, vector search disabled for compatibility")

CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "memory_vectors"

class VectorStore:
    def __init__(self, persist_dir: str = None, embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir or str(CHROMA_PERSIST_DIR)
        self.embedding_model_name = embedding_model
        self._client = None
        self._collection = None
        self._embedding_model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        if self._initialized:
            return
        
        if not CHROMADB_AVAILABLE:
            print("Warning: chromadb not available, vector search disabled")
            self._initialized = True
            return
        
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            
            if EMBEDDINGS_AVAILABLE:
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
            
            self._initialized = True
            print(f"VectorStore initialized: {self.persist_dir}")
        except Exception as e:
            print(f"Warning: Failed to initialize VectorStore: {e}")
            self._initialized = True
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        if not EMBEDDINGS_AVAILABLE or not self._embedding_model:
            return None
        
        try:
            embedding = self._embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}")
            return None
    
    def add_vector(
        self, 
        memory_id: str, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        self._ensure_initialized()
        
        if not self._collection:
            return None
        
        try:
            embedding = self._get_embedding(text)
            if not embedding:
                return None
            
            self._collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
            
            return memory_id
        except Exception as e:
            print(f"Warning: Failed to add vector: {e}")
            return None
    
    def add_vectors_batch(
        self,
        memory_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> List[str]:
        self._ensure_initialized()
        
        if not self._collection or not texts:
            return []
        
        try:
            embeddings = []
            valid_ids = []
            valid_texts = []
            valid_metadatas = []
            
            for i, text in enumerate(texts):
                embedding = self._get_embedding(text)
                if embedding:
                    embeddings.append(embedding)
                    valid_ids.append(memory_ids[i])
                    valid_texts.append(text)
                    valid_metadatas.append(metadatas[i] if metadatas else {})
            
            if embeddings:
                self._collection.add(
                    ids=valid_ids,
                    embeddings=embeddings,
                    documents=valid_texts,
                    metadatas=valid_metadatas
                )
            
            return valid_ids
        except Exception as e:
            print(f"Warning: Failed to add vectors batch: {e}")
            return []
    
    def search(
        self, 
        query_text: str, 
        n_results: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        self._ensure_initialized()
        
        if not self._collection:
            return []
        
        try:
            query_embedding = self._get_embedding(query_text)
            if not query_embedding:
                return []
            
            where_filter = None
            if filter_dict:
                where_filter = {}
                for key, value in filter_dict.items():
                    where_filter[key] = value
            
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results.get("ids"):
                return []
            
            memories = []
            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            
            for i, memory_id in enumerate(ids):
                similarity = 1.0 - distances[i] if distances else 0.5
                metadata = metadatas[i] if metadatas else {}
                memories.append((memory_id, similarity, metadata))
            
            return memories
        except Exception as e:
            print(f"Warning: Failed to search vectors: {e}")
            return []
    
    def search_by_user(
        self,
        user_id: str,
        query_text: str,
        n_results: int = 5
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        return self.search(
            query_text=query_text,
            n_results=n_results,
            filter_dict={"user_id": user_id}
        )
    
    def delete_vector(self, memory_id: str) -> bool:
        self._ensure_initialized()
        
        if not self._collection:
            return False
        
        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Warning: Failed to delete vector: {e}")
            return False
    
    def delete_vectors_by_user(self, user_id: str) -> int:
        self._ensure_initialized()
        
        if not self._collection:
            return 0
        
        try:
            results = self._collection.get(
                where={"user_id": user_id}
            )
            
            if results and results.get("ids"):
                self._collection.delete(ids=results["ids"])
                return len(results["ids"])
            
            return 0
        except Exception as e:
            print(f"Warning: Failed to delete vectors by user: {e}")
            return 0
    
    def update_vector(
        self, 
        memory_id: str, 
        new_text: str,
        new_metadata: Dict[str, Any] = None
    ) -> bool:
        self._ensure_initialized()
        
        if not self._collection:
            return False
        
        try:
            self.delete_vector(memory_id)
            return self.add_vector(memory_id, new_text, new_metadata) is not None
        except Exception as e:
            print(f"Warning: Failed to update vector: {e}")
            return False
    
    def get_vector_count(self) -> int:
        self._ensure_initialized()
        
        if not self._collection:
            return 0
        
        try:
            return self._collection.count()
        except Exception as e:
            print(f"Warning: Failed to get vector count: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        self._ensure_initialized()
        
        return {
            "available": CHROMADB_AVAILABLE and self._collection is not None,
            "embeddings_available": EMBEDDINGS_AVAILABLE,
            "persist_dir": self.persist_dir,
            "collection_name": COLLECTION_NAME,
            "vector_count": self.get_vector_count(),
            "embedding_model": self.embedding_model_name
        }

vector_store = VectorStore()
