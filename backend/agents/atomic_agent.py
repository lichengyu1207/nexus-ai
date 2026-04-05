"""
基于思维原子的智能体决策系统
"""

import logging
from typing import Dict, Any, List, Optional

from backend.agents.atomic_extractor import extract_atoms
from backend.agents.atomic_library import add_atoms
from backend.agents.atomic_injector import inject_atoms, generate_response_with_atoms

logger = logging.getLogger(__name__)


class AtomicAgent:
    """基于思维原子的智能体"""
    
    def __init__(self):
        pass
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """处理用户上传的文本，提取思维原子
        
        Args:
            text: 用户上传的文本
            
        Returns:
            提取结果
        """
        logger.info(f"处理用户文本，长度: {len(text)}")
        
        # 提取思维原子
        atoms = extract_atoms(text)
        
        # 存储到原子库
        atom_ids = add_atoms(atoms)
        
        # 准备返回结果
        result = {
            "atoms": [
                {
                    "name": atom.name,
                    "description": atom.description,
                    "keywords": atom.keywords,
                    "scenario": atom.scenario,
                    "weight": atom.weight
                }
                for atom in atoms
            ],
            "atom_ids": atom_ids,
            "message": f"成功提取并存储 {len(atoms)} 个思维原子"
        }
        
        logger.info(f"文本处理完成，提取 {len(atoms)} 个思维原子")
        return result
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理用户查询，注入思维原子并生成回答
        
        Args:
            query: 用户查询
            
        Returns:
            回答结果
        """
        logger.info(f"处理用户查询: {query}")
        
        # 注入思维原子
        system_prompt, injected_atoms = inject_atoms(query)
        
        # 生成智能体回答
        agent_response = self._generate_response(query, system_prompt)
        
        # 生成包含原子引用的响应
        final_response = generate_response_with_atoms(query, agent_response, injected_atoms)
        
        # 准备返回结果
        result = {
            "query": query,
            "response": final_response,
            "injected_atoms": injected_atoms,
            "system_prompt": system_prompt
        }
        
        logger.info(f"查询处理完成，注入 {len(injected_atoms)} 个思维原子")
        return result
    
    def _generate_response(self, query: str, system_prompt: str) -> str:
        """生成智能体回答
        
        Args:
            query: 用户查询
            system_prompt: 系统提示词
            
        Returns:
            智能体回答
        """
        # 这里应该调用实际的大语言模型
        # 由于环境限制，我们使用模拟回答
        logger.info("使用模拟智能体生成回答")
        
        # 基于查询和系统提示词生成模拟回答
        if "市场竞争策略" in query:
            return "根据'知己知彼'的原则，制定市场竞争策略应首先进行详细的竞品分析，包括对手的产品定位、价格策略、市场份额等；其次要客观评估自身的核心优势和资源；最后结合市场环境，找到差异化切入点。具体来说，您可以采取以下步骤：1. 建立竞品监测机制；2. SWOT分析；3. 细分市场选择。"
        elif "知己知彼" in system_prompt:
            return "'知己知彼，百战不殆'是一个重要的决策原则，意味着在任何竞争或决策情境中，充分了解双方情况是取得成功的关键。这一原则适用于市场竞争、个人发展等多个领域。"
        elif "市场" in query:
            return "市场分析需要综合考虑多个因素，包括市场规模、增长趋势、竞争格局、消费者行为等。建议您采用数据驱动的方法，结合行业报告和市场调研，制定更加精准的市场策略。"
        else:
            return "根据您的问题，我建议您考虑以下几个方面：1. 明确目标和需求；2. 收集相关信息和数据；3. 分析各种可能的方案；4. 评估风险和收益；5. 做出决策并执行。"


# 全局智能体实例
atomic_agent: Optional[AtomicAgent] = None


def get_atomic_agent() -> AtomicAgent:
    """获取原子智能体实例"""
    global atomic_agent
    if atomic_agent is None:
        atomic_agent = AtomicAgent()
    return atomic_agent


async def process_text(text: str) -> Dict[str, Any]:
    """处理用户上传的文本"""
    agent = get_atomic_agent()
    return await agent.process_text(text)


async def process_query(query: str) -> Dict[str, Any]:
    """处理用户查询"""
    agent = get_atomic_agent()
    return await agent.process_query(query)
