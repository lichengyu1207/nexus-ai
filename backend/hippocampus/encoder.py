"""
海马体记忆中枢系统 - 记忆编码器
将原始信息转化为可存储的记忆单元
"""
import uuid
import json
import re
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

@dataclass
class MemoryUnit:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    type: str = "episodic"
    content: str = ""
    summary: str = ""
    importance: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "unknown"
    agents: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_access: str = ""
    embedding_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'summary': self.summary,
            'importance': self.importance,
            'timestamp': self.timestamp,
            'source': self.source,
            'agents': json.dumps(self.agents, ensure_ascii=False),
            'entities': json.dumps(self.entities, ensure_ascii=False),
            'context': json.dumps(self.context, ensure_ascii=False),
            'access_count': self.access_count,
            'last_access': self.last_access,
            'embedding_id': self.embedding_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryUnit':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            type=data.get('type', 'episodic'),
            content=data.get('content', ''),
            summary=data.get('summary', ''),
            importance=data.get('importance', 0.5),
            timestamp=data.get('timestamp', datetime.utcnow().isoformat()),
            source=data.get('source', 'unknown'),
            agents=json.loads(data.get('agents', '[]')) if isinstance(data.get('agents'), str) else data.get('agents', []),
            entities=json.loads(data.get('entities', '[]')) if isinstance(data.get('entities'), str) else data.get('entities', []),
            context=json.loads(data.get('context', '{}')) if isinstance(data.get('context'), str) else data.get('context', {}),
            access_count=data.get('access_count', 0),
            last_access=data.get('last_access', ''),
            embedding_id=data.get('embedding_id', ''),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat()),
        )

MEMORY_TYPE_EPISODIC = "episodic"
MEMORY_TYPE_SEMANTIC = "semantic"
MEMORY_TYPE_PROCEDURAL = "procedural"

IMPORTANCE_KEYWORDS_HIGH = [
    "非常重要", "关键", "核心", "必须", "紧急", "优先",
    "喜欢", "讨厌", "偏好", "决定", "选择", "购买",
    "预算", "价格", "贷款", "首付", "投资",
]

IMPORTANCE_KEYWORDS_MEDIUM = [
    "考虑", "比较", "关注", "需要", "想要",
    "问题", "疑问", "咨询", "建议",
]

ENTITY_PATTERNS = {
    'city': r'(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆|天津|苏州|厦门|长沙|郑州|东莞|青岛|沈阳|合肥|佛山|济南|哈尔滨|温州|长春|石家庄|常州|福州|昆明|烟台|宁波|南通|潍坊|台州|珠海|徐州|太原|惠州|威海|嘉兴|中山|保定|金华|泉州|临沂|江门|湛江|韶关|株洲|湘潭)',
    'price': r'(\d+(?:\.\d+)?(?:万|百万|千万|亿|w|W))',
    'area': r'(\d+(?:\.\d+)?(?:平米|平方米|㎡|平|方))',
    'room': r'(\d+室\d+厅|\d+房|\d+居)',
    'year': r'((?:19|20)\d{2}年?)',
    'phone': r'(1[3-9]\d{9})',
    'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
}

class MemoryEncoder:
    def __init__(self):
        self.entity_patterns = ENTITY_PATTERNS
        self.importance_keywords_high = IMPORTANCE_KEYWORDS_HIGH
        self.importance_keywords_medium = IMPORTANCE_KEYWORDS_MEDIUM
    
    def encode(
        self,
        user_id: str,
        content: str,
        source: str = "consult",
        agents: List[str] = None,
        context: Dict[str, Any] = None,
        memory_type: str = None
    ) -> MemoryUnit:
        entities = self.extract_entities(content)
        
        summary = self.generate_summary(content)
        
        importance = self.compute_importance(content, context)
        
        if memory_type is None:
            memory_type = self._infer_memory_type(content, source)
        
        memory = MemoryUnit(
            user_id=user_id,
            type=memory_type,
            content=content,
            summary=summary,
            importance=importance,
            source=source,
            agents=agents or [],
            entities=entities,
            context=context or {},
        )
        
        return memory
    
    def extract_entities(self, text: str) -> List[str]:
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and match not in entities:
                    entities.append(match)
        
        custom_entities = self._extract_custom_entities(text)
        for entity in custom_entities:
            if entity not in entities:
                entities.append(entity)
        
        return entities[:20]
    
    def _extract_custom_entities(self, text: str) -> List[str]:
        entities = []
        
        location_patterns = [
            r'([\u4e00-\u9fa5]{2,}(?:市|区|县|镇|街道|路|街|小区|花园|广场|大厦|公寓|新城|名苑|华府|府邸|雅苑|豪庭|花园))',
            r'([\u4e00-\u9fa5]{2,}(?:地铁|公交|学校|医院|商场|公园|银行|超市))',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return list(set(entities))[:10]
    
    def generate_summary(self, text: str, max_length: int = 100) -> str:
        text = text.strip()
        
        if len(text) <= max_length:
            return text
        
        sentences = re.split(r'[。！？\n]', text)
        
        if len(sentences) > 1:
            summary_parts = []
            current_length = 0
            
            for sentence in sentences:
                if current_length + len(sentence) <= max_length:
                    summary_parts.append(sentence)
                    current_length += len(sentence) + 1
                else:
                    break
            
            summary = '。'.join(summary_parts)
            if summary and not summary.endswith('。'):
                summary += '。'
            return summary
        
        return text[:max_length-3] + '...'
    
    def compute_importance(
        self,
        content: str,
        context: Dict[str, Any] = None
    ) -> float:
        importance = 0.3
        
        content_lower = content.lower()
        
        for keyword in self.importance_keywords_high:
            if keyword in content_lower:
                importance += 0.15
                break
        
        for keyword in self.importance_keywords_medium:
            if keyword in content_lower:
                importance += 0.1
                break
        
        if context:
            if context.get('user_emotion') == 'positive':
                importance += 0.1
            elif context.get('user_emotion') == 'negative':
                importance += 0.15
            
            if context.get('is_decision'):
                importance += 0.2
            
            if context.get('is_preference'):
                importance += 0.15
        
        if re.search(r'\d+万|\d+百万|\d+千万', content):
            importance += 0.1
        
        if re.search(r'预算|价格|贷款|首付', content):
            importance += 0.1
        
        return min(1.0, max(0.0, importance))
    
    def _infer_memory_type(self, content: str, source: str) -> str:
        if source in ['consult', 'dialogue', 'chat']:
            return MEMORY_TYPE_EPISODIC
        
        if source in ['analysis', 'report', 'knowledge']:
            return MEMORY_TYPE_SEMANTIC
        
        if source in ['task', 'workflow', 'procedure']:
            return MEMORY_TYPE_PROCEDURAL
        
        if re.search(r'我|我们|今天|刚才|刚才', content):
            return MEMORY_TYPE_EPISODIC
        
        if re.search(r'是|定义为|意味着|包括', content):
            return MEMORY_TYPE_SEMANTIC
        
        return MEMORY_TYPE_EPISODIC
    
    def encode_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        session_id: str = None,
        agents: List[str] = None
    ) -> MemoryUnit:
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        context = {
            'session_id': session_id,
            'message_count': len(messages),
        }
        
        return self.encode(
            user_id=user_id,
            content=conversation_text,
            source="consult",
            agents=agents,
            context=context,
            memory_type=MEMORY_TYPE_EPISODIC
        )
    
    def encode_fact(
        self,
        user_id: str,
        fact: str,
        category: str = None,
        agents: List[str] = None
    ) -> MemoryUnit:
        context = {'category': category} if category else {}
        
        return self.encode(
            user_id=user_id,
            content=fact,
            source="knowledge",
            agents=agents,
            context=context,
            memory_type=MEMORY_TYPE_SEMANTIC
        )
    
    def encode_preference(
        self,
        user_id: str,
        preference: str,
        category: str = None,
        agents: List[str] = None
    ) -> MemoryUnit:
        context = {
            'category': category,
            'is_preference': True,
        }
        
        memory = self.encode(
            user_id=user_id,
            content=preference,
            source="preference",
            agents=agents,
            context=context,
            memory_type=MEMORY_TYPE_SEMANTIC
        )
        
        memory.importance = max(memory.importance, 0.7)
        
        return memory

memory_encoder = MemoryEncoder()
