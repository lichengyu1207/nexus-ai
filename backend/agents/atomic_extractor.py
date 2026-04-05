"""
思维原子提取模块
从文本中提取思维框架、价值主张或文化元素
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 延迟导入可能不兼容的库
transformers = None
BertTokenizer = None
BertModel = None
torch = None

logger = logging.getLogger(__name__)

try:
    from transformers import BertTokenizer, BertModel
    import torch
except Exception as e:
    logger.warning(f"BERT模型导入失败: {e}")


@dataclass
class ThoughtAtom:
    """思维原子"""
    name: str  # 原子名称
    description: str  # 原子描述
    keywords: List[str]  # 关键词
    scenario: List[str]  # 应用场景
    weight: float  # 初始权重 (0.0-1.0)
    vector: Optional[List[float]] = None  # 向量表示
    metadata: Optional[Dict[str, Any]] = None  # 元数据


class AtomicExtractor:
    """思维原子提取器"""
    
    def __init__(self, model_name: str = "bert-base-chinese"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.initialize_model()
    
    def initialize_model(self):
        """初始化BERT模型"""
        try:
            if BertTokenizer and BertModel:
                self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
                self.model = BertModel.from_pretrained(self.model_name)
                logger.info("BERT模型初始化成功")
            else:
                logger.warning("BERT模型不可用，使用基于规则的提取")
        except Exception as e:
            logger.error(f"初始化BERT模型失败: {e}")
    
    def extract_atoms(self, text: str) -> List[ThoughtAtom]:
        """从文本中提取思维原子
        
        Args:
            text: 输入文本
            
        Returns:
            思维原子列表
        """
        logger.info(f"开始提取思维原子，文本长度: {len(text)}")
        
        # 使用大语言模型提取思维原子
        atoms = self._extract_with_llm(text)
        
        # 如果LLM提取失败，使用基于规则的提取
        if not atoms:
            atoms = self._extract_with_rules(text)
        
        logger.info(f"提取完成，共提取 {len(atoms)} 个思维原子")
        return atoms
    
    def _extract_with_llm(self, text: str) -> List[ThoughtAtom]:
        """使用大语言模型提取思维原子"""
        try:
            # 构建提示词
            prompt = f"请从以下文本中提取出思维框架、价值主张或文化元素，以JSON格式输出，包含name、description、keywords、scenario、weight字段。\n\n文本：{text}"
            
            # 这里应该调用实际的大语言模型
            # 由于环境限制，我们使用模拟输出
            logger.info("使用模拟LLM提取思维原子")
            
            # 模拟LLM输出
            mock_output = self._mock_llm_output(text)
            
            # 解析输出
            atoms = self._parse_llm_output(mock_output)
            return atoms
        except Exception as e:
            logger.error(f"使用LLM提取思维原子失败: {e}")
            return []
    
    def _mock_llm_output(self, text: str) -> str:
        """模拟LLM输出"""
        # 基于文本内容生成模拟输出
        if "孙子兵法" in text or "知己知彼" in text:
            return '''
{
  "atoms": [
    {
      "name": "知彼知己",
      "description": "充分了解敌我双方情况才能取得胜利",
      "keywords": ["知己知彼", "情报", "分析"],
      "scenario": ["竞争分析", "风险评估"],
      "weight": 0.8
    },
    {
      "name": "百战不殆",
      "description": "多次作战都不会失败",
      "keywords": ["百战不殆", "胜利", "策略"],
      "scenario": ["战略规划", "风险管理"],
      "weight": 0.7
    }
  ]
}
            '''
        elif "市场" in text and "竞争" in text:
            return '''
{
  "atoms": [
    {
      "name": "市场定位",
      "description": "明确产品在市场中的位置",
      "keywords": ["市场定位", "目标客户", "差异化"],
      "scenario": ["产品开发", "市场策略"],
      "weight": 0.85
    }
  ]
}
            '''
        else:
            return '''
{
  "atoms": [
    {
      "name": "通用原则",
      "description": "从文本中提取的通用思维原则",
      "keywords": ["原则", "思维", "方法"],
      "scenario": ["决策", "规划"],
      "weight": 0.7
    }
  ]
}
            '''
    
    def _parse_llm_output(self, output: str) -> List[ThoughtAtom]:
        """解析LLM输出"""
        try:
            data = json.loads(output)
            atoms_data = data.get("atoms", [])
            atoms = []
            
            for atom_data in atoms_data:
                atom = ThoughtAtom(
                    name=atom_data.get("name", ""),
                    description=atom_data.get("description", ""),
                    keywords=atom_data.get("keywords", []),
                    scenario=atom_data.get("scenario", []),
                    weight=atom_data.get("weight", 0.5)
                )
                # 生成向量表示
                atom.vector = self._generate_vector(atom)
                atoms.append(atom)
            
            return atoms
        except Exception as e:
            logger.error(f"解析LLM输出失败: {e}")
            return []
    
    def _extract_with_rules(self, text: str) -> List[ThoughtAtom]:
        """基于规则提取思维原子"""
        logger.info("使用基于规则的方法提取思维原子")
        
        # 简单的规则提取
        atoms = []
        
        # 检查常见的思维框架
        if "知己知彼" in text:
            atom = ThoughtAtom(
                name="知彼知己",
                description="充分了解敌我双方情况才能取得胜利",
                keywords=["知己知彼", "情报", "分析"],
                scenario=["竞争分析", "风险评估"],
                weight=0.8
            )
            atom.vector = self._generate_vector(atom)
            atoms.append(atom)
        
        if "百战不殆" in text:
            atom = ThoughtAtom(
                name="百战不殆",
                description="多次作战都不会失败",
                keywords=["百战不殆", "胜利", "策略"],
                scenario=["战略规划", "风险管理"],
                weight=0.7
            )
            atom.vector = self._generate_vector(atom)
            atoms.append(atom)
        
        if not atoms:
            # 生成默认原子
            atom = ThoughtAtom(
                name="通用原则",
                description="从文本中提取的通用思维原则",
                keywords=["原则", "思维", "方法"],
                scenario=["决策", "规划"],
                weight=0.7
            )
            atom.vector = self._generate_vector(atom)
            atoms.append(atom)
        
        return atoms
    
    def _generate_vector(self, atom: ThoughtAtom) -> List[float]:
        """生成原子的向量表示"""
        try:
            if self.model and self.tokenizer:
                # 使用BERT生成向量
                text = f"{atom.name} {atom.description} {' '.join(atom.keywords)} {' '.join(atom.scenario)}"
                inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                # 使用[CLS] token的嵌入
                vector = outputs.last_hidden_state[:, 0, :].squeeze().numpy().tolist()
                return vector
            else:
                # 基于规则生成向量
                return self._generate_rule_based_vector(atom)
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            # 返回随机向量作为回退
            return [0.0] * 768
    
    def _generate_rule_based_vector(self, atom: ThoughtAtom) -> List[float]:
        """基于规则生成向量"""
        # 简单的基于规则的向量生成
        vector = [0.0] * 768
        
        # 基于关键词生成向量
        keyword_weights = {
            "知己知彼": 0.8,
            "情报": 0.7,
            "分析": 0.6,
            "竞争": 0.7,
            "风险": 0.6,
            "策略": 0.8,
            "规划": 0.7,
            "决策": 0.8
        }
        
        # 填充向量
        for i, keyword in enumerate(atom.keywords):
            if keyword in keyword_weights and i < 768:
                vector[i] = keyword_weights[keyword]
        
        # 基于场景生成向量
        for i, scene in enumerate(atom.scenario):
            if i + len(atom.keywords) < 768:
                vector[i + len(atom.keywords)] = 0.5
        
        # 基于权重调整向量
        for i in range(len(vector)):
            vector[i] *= atom.weight
        
        return vector
    
    def validate_atom(self, atom: ThoughtAtom) -> bool:
        """验证思维原子的有效性"""
        if not atom.name or not atom.description:
            return False
        if not atom.keywords or len(atom.keywords) == 0:
            return False
        if not atom.scenario or len(atom.scenario) == 0:
            return False
        if atom.weight < 0.0 or atom.weight > 1.0:
            return False
        return True


# 全局提取器实例
atomic_extractor: Optional[AtomicExtractor] = None


def get_atomic_extractor() -> AtomicExtractor:
    """获取原子提取器实例"""
    global atomic_extractor
    if atomic_extractor is None:
        atomic_extractor = AtomicExtractor()
    return atomic_extractor


def extract_atoms(text: str) -> List[ThoughtAtom]:
    """提取思维原子"""
    extractor = get_atomic_extractor()
    return extractor.extract_atoms(text)
