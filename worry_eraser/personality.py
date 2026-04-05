"""
人格引擎模块
基于房都督平台的人格化引擎，为烦恼橡皮擦提供智能体回复
"""

import random
from typing import List, Dict, Optional
from prompts.consolation import ZHOUYU_PROMPT, LUXUN_PROMPT, QUICK_REPLIES

def get_response(agent, user_message, history_memories):
    """
    获取智能体回复
    
    Args:
        agent: 智能体名称 (zhouyu 或 luxun)
        user_message: 用户消息
        history_memories: 历史记忆列表
    
    Returns:
        智能体回复文本
    """
    # 检查是否有相似的历史记忆
    similar_memory = _find_similar_memory(user_message, history_memories)
    
    # 生成回复
    if agent == "zhouyu":
        return _generate_zhouyu_response(user_message, similar_memory)
    elif agent == "luxun":
        return _generate_luxun_response(user_message, similar_memory)
    else:
        return "抱歉，我不认识这个智能体。"

def _find_similar_memory(user_message, memories):
    """
    查找相似的历史记忆
    
    Args:
        user_message: 用户消息
        memories: 历史记忆列表
    
    Returns:
        相似的记忆，或 None
    """
    # 简单的关键词匹配
    keywords = _extract_keywords(user_message)
    
    for memory in memories:
        memory_text = memory.get("user_message", "")
        memory_keywords = _extract_keywords(memory_text)
        
        # 检查是否有共同关键词
        common_keywords = set(keywords) & set(memory_keywords)
        if common_keywords:
            return memory
    
    return None

def _extract_keywords(text):
    """
    提取关键词
    
    Args:
        text: 文本
    
    Returns:
        关键词列表
    """
    # 简单的关键词提取
    keywords = [
        "压力", "烦恼", "焦虑", "工作", "学习", "生活", "家庭",
        "朋友", "健康", "未来", "困难", "问题", "挫折", "迷茫"
    ]
    
    extracted = []
    for keyword in keywords:
        if keyword in text:
            extracted.append(keyword)
    
    return extracted

def _generate_zhouyu_response(user_message, similar_memory):
    """
    生成周瑜的回复
    
    Args:
        user_message: 用户消息
        similar_memory: 相似的历史记忆
    
    Returns:
        回复文本
    """
    # 检查是否有相似记忆
    if similar_memory:
        # 引用历史记忆
        previous_issue = similar_memory.get("user_message", "")[:30] + "..."
        reply = f"公瑾：上次你提到{previous_issue}，现在好些了吗？人生如江流，时急时缓，烦恼不过一时之浪。且听我抚一曲《高山流水》，让心随音静。"
    else:
        # 随机选择快速回复
        reply = random.choice(QUICK_REPLIES["zhouyu"])
    
    return reply

def _generate_luxun_response(user_message, similar_memory):
    """
    生成陆逊的回复
    
    Args:
        user_message: 用户消息
        similar_memory: 相似的历史记忆
    
    Returns:
        回复文本
    """
    # 检查是否有相似记忆
    if similar_memory:
        # 引用历史记忆
        previous_issue = similar_memory.get("user_message", "")[:30] + "..."
        reply = f"伯言：上次你提到{previous_issue}，我一直在思考。昔夷陵之战，刘备意气用事，终致大败。烦恼之事，不妨退一步，待云开雾散。"
    else:
        # 随机选择快速回复
        reply = random.choice(QUICK_REPLIES["luxun"])
    
    return reply

def get_agent_info(agent):
    """
    获取智能体信息
    
    Args:
        agent: 智能体名称
    
    Returns:
        智能体信息字典
    """
    agents_info = {
        "zhouyu": {
            "name": "周瑜",
            "title": "吴国大都督",
            "personality": "豪迈、豁达、富有诗意",
            "avatar": "🎵"
        },
        "luxun": {
            "name": "陆逊",
            "title": "吴国大都督",
            "personality": "沉稳、细腻、深思熟虑",
            "avatar": "📜"
        }
    }
    
    return agents_info.get(agent, {
        "name": "未知",
        "title": "",
        "personality": "",
        "avatar": "❓"
    })