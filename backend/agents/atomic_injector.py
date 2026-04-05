"""
思维原子注入模块
将检索到的思维原子转化为系统提示词并注入到智能体中
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.atomic_extractor import ThoughtAtom
from backend.agents.atomic_library import search_atoms

logger = logging.getLogger(__name__)


class AtomicInjector:
    """思维原子注入器"""
    
    def __init__(self):
        pass
    
    def inject_atoms(self, query: str, top_k: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
        """注入思维原子
        
        Args:
            query: 用户查询
            top_k: 注入的原子数量
            
        Returns:
            (系统提示词, 注入的原子列表)
        """
        logger.info(f"开始注入思维原子，查询: {query}")
        
        # 检索相关思维原子
        atoms_with_score = search_atoms(query, top_k=top_k)
        
        # 生成系统提示词
        system_prompt = self._generate_system_prompt(atoms_with_score)
        
        # 准备注入的原子信息
        injected_atoms = []
        for atom, similarity in atoms_with_score:
            atom_info = {
                "name": atom.name,
                "description": atom.description,
                "keywords": atom.keywords,
                "scenario": atom.scenario,
                "weight": atom.weight,
                "similarity": similarity
            }
            injected_atoms.append(atom_info)
        
        logger.info(f"注入完成，共注入 {len(injected_atoms)} 个思维原子")
        return system_prompt, injected_atoms
    
    def _generate_system_prompt(self, atoms_with_score: List[Tuple[ThoughtAtom, float]]) -> str:
        """生成系统提示词
        
        Args:
            atoms_with_score: 思维原子和相似度列表
            
        Returns:
            系统提示词
        """
        if not atoms_with_score:
            return ""
        
        prompt_parts = []
        prompt_parts.append("决策原则：")
        
        for atom, similarity in atoms_with_score:
            # 只注入相似度高于阈值的原子
            if similarity < 0.6:
                continue
            
            # 生成原子提示
            atom_prompt = f"{atom.name}：{atom.description}"
            prompt_parts.append(atom_prompt)
        
        # 添加应用场景提示
        prompt_parts.append("\n在回答用户问题时，请结合上述决策原则进行分析和推理。")
        
        return " ".join(prompt_parts)
    
    def generate_response_with_atoms(self, user_query: str, agent_response: str, injected_atoms: List[Dict[str, Any]]) -> str:
        """生成包含思维原子引用的响应
        
        Args:
            user_query: 用户查询
            agent_response: 智能体原始响应
            injected_atoms: 注入的原子列表
            
        Returns:
            包含思维原子引用的响应
        """
        # 添加原子引用信息
        if injected_atoms:
            atom_references = []
            for atom in injected_atoms:
                if atom["similarity"] >= 0.7:
                    atom_references.append(atom["name"])
            
            if atom_references:
                reference_text = f"\n\n决策依据：本次回答引用了思维原子 '{', '.join(atom_references)}'"
                agent_response += reference_text
        
        return agent_response
    
    def process_user_feedback(self, atom_id: str, is_useful: bool):
        """处理用户反馈
        
        Args:
            atom_id: 原子ID
            is_useful: 是否有用
        """
        from backend.agents.atomic_library import get_atom, update_atom_weight
        
        atom = get_atom(atom_id)
        if atom:
            # 根据反馈调整权重
            new_weight = atom.weight
            if is_useful:
                new_weight = min(1.0, atom.weight + 0.1)
            else:
                new_weight = max(0.1, atom.weight - 0.1)
            
            # 更新权重
            update_atom_weight(atom_id, new_weight)
            logger.info(f"处理用户反馈: 原子 {atom.name} 权重调整为 {new_weight}")
        else:
            logger.warning(f"处理用户反馈失败: 找不到原子 {atom_id}")


# 全局注入器实例
atomic_injector: Optional[AtomicInjector] = None


def get_atomic_injector() -> AtomicInjector:
    """获取原子注入器实例"""
    global atomic_injector
    if atomic_injector is None:
        atomic_injector = AtomicInjector()
    return atomic_injector


def inject_atoms(query: str, top_k: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
    """注入思维原子"""
    injector = get_atomic_injector()
    return injector.inject_atoms(query, top_k)


def generate_response_with_atoms(user_query: str, agent_response: str, injected_atoms: List[Dict[str, Any]]) -> str:
    """生成包含思维原子引用的响应"""
    injector = get_atomic_injector()
    return injector.generate_response_with_atoms(user_query, agent_response, injected_atoms)


def process_user_feedback(atom_id: str, is_useful: bool):
    """处理用户反馈"""
    injector = get_atomic_injector()
    injector.process_user_feedback(atom_id, is_useful)
