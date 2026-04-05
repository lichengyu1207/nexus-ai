#!/usr/bin/env python3
"""
人格库模块
"""

import json
import os
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# 延迟导入可能不兼容的库
transformers = None
BertTokenizer = None
BertModel = None
torch = None


try:
    from transformers import BertTokenizer, BertModel
    import torch
except Exception as e:
    print(f"BERT模型导入失败: {e}")


@dataclass
class Personality:
    """人物人格特征"""
    personality_id: str  # 人格ID
    name: str  # 人物名称
    era: str  # 时代背景
    source: str  # 来源文献
    personality_dimensions: Dict[str, float]  # 性格维度，每个维度取值0-1
    language_style: Dict[str, Any]  # 语言风格：用词倾向、句式复杂度、修辞手法
    knowledge_domains: List[str]  # 知识域：关键词列表
    emotional_templates: Dict[str, List[str]]  # 情感模板：不同情绪下的典型表达方式
    embedding: Optional[List[float]] = None  # 768维向量
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据


class PersonalityLibrary:
    """人格库"""
    
    def __init__(self, storage_path: str = None):
        # 存储路径
        if storage_path:
            self.storage_path = storage_path
        else:
            current_dir = os.path.abspath(__file__)
            parent_dir = os.path.dirname(current_dir)
            grandparent_dir = os.path.dirname(parent_dir)
            great_grandparent_dir = os.path.dirname(grandparent_dir)
            self.storage_path = os.path.join(great_grandparent_dir, "data", "personality")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 初始化BERT模型
        self._init_bert_model()
        
        # 人格库存储
        self.personalities = {}
        self._load_personalities()
    
    def _init_bert_model(self):
        """初始化BERT模型"""
        try:
            if BertTokenizer and BertModel:
                self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
                self.bert_model = BertModel.from_pretrained('bert-base-chinese')
                self.bert_model.eval()
                print("BERT模型初始化成功")
            else:
                raise ImportError("BERT model not available")
        except Exception as e:
            print(f"BERT模型初始化失败，将使用字符频率嵌入: {e}")
            self.tokenizer = None
            self.bert_model = None
    
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
            print(f"生成嵌入向量失败: {e}")
            # 出错时返回零向量
            return [0.0] * 768
    
    def _load_personalities(self):
        """加载人格库"""
        try:
            for filename in os.listdir(self.storage_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.storage_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        personality = Personality(**data)
                        self.personalities[personality.name] = personality
            print(f"加载了 {len(self.personalities)} 个人格特征")
        except Exception as e:
            print(f"加载人格库失败: {e}")
    
    def _save_personality(self, personality: Personality):
        """保存人格特征"""
        try:
            file_path = os.path.join(self.storage_path, f"{personality.name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(personality.__dict__, f, ensure_ascii=False, indent=2)
            print(f"人格特征 {personality.name} 保存成功")
        except Exception as e:
            print(f"保存人格特征失败: {e}")
    
    def add_personality(self, personality: Personality):
        """添加人格特征"""
        # 生成嵌入向量
        personality_text = " ".join([
            personality.name,
            personality.era,
            " ".join([f"{k}:{v}" for k, v in personality.personality_dimensions.items()]),
            " ".join([f"{k}:{v}" for k, v in personality.language_style.items()]),
            " ".join(personality.knowledge_domains),
            " ".join([f"{emotion}:{' '.join(templates)}" for emotion, templates in personality.emotional_templates.items()])
        ])
        personality.embedding = self._get_embedding(personality_text)
        
        # 存储人格特征
        self.personalities[personality.name] = personality
        self._save_personality(personality)
        return personality
    
    def get_personality(self, name: str) -> Optional[Personality]:
        """获取人格特征"""
        return self.personalities.get(name)
    
    def list_personalities(self) -> List[str]:
        """列出所有人格特征"""
        return list(self.personalities.keys())
    
    def search_similar_personalities(self, query: str, top_k: int = 5) -> List[tuple]:
        """搜索相似的人格特征"""
        try:
            # 生成查询向量
            query_embedding = self._get_embedding(query)
            
            # 计算相似度
            similarities = []
            for name, personality in self.personalities.items():
                if personality.embedding:
                    similarity = np.dot(query_embedding, personality.embedding)
                    similarities.append((name, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        except Exception as e:
            print(f"搜索相似人格特征失败: {e}")
            return []
