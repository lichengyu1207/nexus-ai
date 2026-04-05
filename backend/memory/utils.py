"""
智能体记忆系统 - 工具函数
提供摘要生成、重要性评分、嵌入生成等辅助功能
"""
import json
import re
from typing import List, Dict, Any, Optional

def generate_summary(text: str, max_length: int = 100) -> str:
    if not text:
        return ""
    
    text = text.strip()
    
    if len(text) <= max_length:
        return text
    
    sentences = re.split(r'[。！？.!?]', text)
    summary = ""
    
    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence + "。"
        else:
            break
    
    if not summary:
        summary = text[:max_length] + "..."
    
    return summary.strip()

def calculate_importance(input_text: str, output_text: str) -> float:
    if not input_text and not output_text:
        return 5.0
    
    importance = 5.0
    
    preference_keywords = ['喜欢', '偏好', '想要', '希望', '预算', '需求', '要求']
    for keyword in preference_keywords:
        if keyword in input_text:
            importance += 1.0
    
    fact_keywords = ['价格', '面积', '位置', '户型', '学区', '地铁']
    for keyword in fact_keywords:
        if keyword in output_text:
            importance += 0.5
    
    decision_keywords = ['决定', '选择', '购买', '投资']
    for keyword in decision_keywords:
        if keyword in input_text or keyword in output_text:
            importance += 1.5
    
    return min(max(importance, 1.0), 10.0)

def extract_preferences(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    
    preferences = {}
    
    budget_pattern = r'预算[：:]\s*(\d+(?:\.\d+)?[万百千万]?)'
    match = re.search(budget_pattern, text)
    if match:
        preferences['budget'] = match.group(1)
    
    area_pattern = r'面积[：:]\s*(\d+(?:\.\d+)?[平平方米]?)'
    match = re.search(area_pattern, text)
    if match:
        preferences['area'] = match.group(1)
    
    location_pattern = r'(?:在|位于|想买)[\s]*([^\s,，。！？]+(?:区|县|市|街道))'
    match = re.search(location_pattern, text)
    if match:
        preferences['location'] = match.group(1)
    
    room_pattern = r'(\d+)[室房]'
    match = re.search(room_pattern, text)
    if match:
        preferences['rooms'] = int(match.group(1))
    
    return preferences

def merge_memories(memories: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not memories:
        return {}
    
    if len(memories) == 1:
        return memories[0]
    
    merged = {
        'id': memories[0].get('id'),
        'user_id': memories[0].get('user_id'),
        'agent_name': memories[0].get('agent_name'),
        'session_id': memories[0].get('session_id'),
        'created_at': max(m.get('created_at', '') for m in memories),
        'input_text': memories[0].get('input_text', ''),
        'output_text': ' | '.join([m.get('output_text', '') for m in memories if m.get('output_text')]),
        'summary': generate_summary(' '.join([m.get('summary', '') for m in memories if m.get('summary')])),
        'importance': max(m.get('importance', 5.0) for m in memories),
        'category': memories[0].get('category', 'fact'),
        'tags': list(set([tag for m in memories for tag in json.loads(m.get('tags', '[]'))])),
        'access_count': sum(m.get('access_count', 0) for m in memories),
    }
    
    return merged

def format_memories_for_prompt(memories: List[Dict[str, Any]], max_length: int = 1000) -> str:
    if not memories:
        return ""
    
    formatted = []
    total_length = 0
    
    for i, memory in enumerate(memories):
        entry = f"[{i+1}] {memory.get('summary', memory.get('input_text', '')[:50])}"
        
        if total_length + len(entry) > max_length:
            break
        
        formatted.append(entry)
        total_length += len(entry)
    
    return "\n".join(formatted)

def categorize_memory(text: str) -> str:
    if not text:
        return 'fact'
    
    preference_keywords = ['喜欢', '偏好', '想要', '希望', '需求', '要求']
    for keyword in preference_keywords:
        if keyword in text:
            return 'preference'
    
    event_keywords = ['看了', '参观', '咨询', '购买', '签约', '成交']
    for keyword in event_keywords:
        if keyword in text:
            return 'event'
    
    return 'fact'

def extract_tags(text: str) -> List[str]:
    if not text:
        return []
    
    tags = []
    
    tag_patterns = [
        (r'(\d+万)', 'budget'),
        (r'(\d+平)', 'area'),
        (r'(\d+室)', 'rooms'),
        (r'([^\s,，。！？]+(?:区|县|市))', 'location'),
        (r'(学区房|地铁房|海景房|江景房)', 'property_type'),
    ]
    
    for pattern, tag_type in tag_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            tags.append(f"{tag_type}:{match}")
    
    return list(set(tags))
