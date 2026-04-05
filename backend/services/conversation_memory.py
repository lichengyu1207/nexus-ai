"""
对话记忆服务
提供持久化的对话记忆存储和检索
"""
import json
import time
import hashlib
from typing import Dict, Any, List, Optional
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """对话记忆管理"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._session_memories: Dict[str, Dict] = {}
        self._user_contexts: Dict[str, Dict] = {}
        self._entity_cache: Dict[str, Dict] = {}
        self._intent_history: Dict[str, List] = defaultdict(list)
        self._max_history = 20
        self._cache_ttl = 3600
        self._last_cleanup = time.time()
    
    def get_or_create_session(self, session_id: str, user_id: str) -> Dict:
        """获取或创建会话记忆"""
        if session_id not in self._session_memories:
            self._session_memories[session_id] = {
                'user_id': user_id,
                'created_at': time.time(),
                'messages': [],
                'entities': {},
                'intent': None,
                'turn_count': 0,
                'context': {}
            }
        
        return self._session_memories[session_id]
    
    def add_message(self, session_id: str, role: str, content: str, 
                    intent: str = None, entities: Dict = None):
        """添加消息到会话记忆"""
        session = self._session_memories.get(session_id)
        if not session:
            return
        
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'intent': intent,
            'entities': entities
        }
        
        session['messages'].append(message)
        session['turn_count'] += 1
        
        if len(session['messages']) > self._max_history * 2:
            session['messages'] = session['messages'][-self._max_history * 2:]
        
        if intent:
            session['intent'] = intent
            self._intent_history[session['user_id']].append(intent)
        
        if entities:
            session['entities'].update(entities)
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """获取对话历史"""
        session = self._session_memories.get(session_id)
        if not session:
            return []
        
        return session['messages'][-limit:]
    
    def get_entities(self, session_id: str) -> Dict:
        """获取会话中提取的所有实体"""
        session = self._session_memories.get(session_id)
        if not session:
            return {}
        
        return session.get('entities', {})
    
    def get_context(self, session_id: str) -> Dict:
        """获取会话上下文"""
        session = self._session_memories.get(session_id)
        if not session:
            return {}
        
        return {
            'intent': session.get('intent'),
            'entities': session.get('entities', {}),
            'turn_count': session.get('turn_count', 0),
            'context': session.get('context', {})
        }
    
    def update_context(self, session_id: str, key: str, value: Any):
        """更新会话上下文"""
        session = self._session_memories.get(session_id)
        if session:
            session['context'][key] = value
    
    def set_user_context(self, user_id: str, context: Dict):
        """设置用户全局上下文"""
        if user_id not in self._user_contexts:
            self._user_contexts[user_id] = {
                'profile': {},
                'preferences': {},
                'last_sessions': [],
                'frequent_intents': [],
                'common_entities': {}
            }
        
        self._user_contexts[user_id].update(context)
    
    def get_user_context(self, user_id: str) -> Dict:
        """获取用户全局上下文"""
        return self._user_contexts.get(user_id, {
            'profile': {},
            'preferences': {},
            'last_sessions': [],
            'frequent_intents': [],
            'common_entities': {}
        })
    
    def get_user_intent_history(self, user_id: str, limit: int = 10) -> List[str]:
        """获取用户意图历史"""
        return self._intent_history.get(user_id, [])[-limit:]
    
    def get_frequent_intent(self, user_id: str) -> Optional[str]:
        """获取用户最常问的意图"""
        intents = self._intent_history.get(user_id, [])
        if not intents:
            return None
        
        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return max(intent_counts, key=intent_counts.get) if intent_counts else None
    
    def merge_entities(self, session_id: str, new_entities: Dict) -> Dict:
        """合并新旧实体"""
        existing = self.get_entities(session_id)
        merged = {**existing, **new_entities}
        
        session = self._session_memories.get(session_id)
        if session:
            session['entities'] = merged
        
        return merged
    
    def get_relevant_context(self, session_id: str, current_intent: str) -> Dict:
        """获取与当前意图相关的上下文"""
        session = self._session_memories.get(session_id)
        if not session:
            return {}
        
        entities = session.get('entities', {})
        history = session.get('messages', [])
        
        relevant_entities = {}
        
        intent_entity_mapping = {
            'house_recommendation': ['city', 'budget', 'rooms', 'house_type'],
            'area_info': ['city', 'district'],
            'price_inquiry': ['city', 'district'],
            'policy': ['city'],
            'loan_calc': ['budget', 'monthly_income'],
            'investment': ['city', 'budget'],
        }
        
        relevant_keys = intent_entity_mapping.get(current_intent, [])
        for key in relevant_keys:
            if key in entities:
                relevant_entities[key] = entities[key]
        
        return {
            'entities': relevant_entities,
            'last_intent': session.get('intent'),
            'turn_count': session.get('turn_count', 0)
        }
    
    def summarize_session(self, session_id: str) -> Dict:
        """总结会话内容"""
        session = self._session_memories.get(session_id)
        if not session:
            return {}
        
        messages = session.get('messages', [])
        user_messages = [m for m in messages if m['role'] == 'user']
        
        return {
            'session_id': session_id,
            'user_id': session.get('user_id'),
            'turn_count': session.get('turn_count', 0),
            'user_message_count': len(user_messages),
            'final_intent': session.get('intent'),
            'collected_entities': session.get('entities', {}),
            'duration': time.time() - session.get('created_at', time.time())
        }
    
    def cleanup_expired(self, max_age: float = 7200):
        """清理过期会话"""
        now = time.time()
        if now - self._last_cleanup < 300:
            return
        
        expired = [
            sid for sid, session in self._session_memories.items()
            if now - session.get('created_at', 0) > max_age
        ]
        
        for sid in expired:
            del self._session_memories[sid]
        
        self._last_cleanup = now
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            'active_sessions': len(self._session_memories),
            'users_with_context': len(self._user_contexts),
            'total_intents_tracked': sum(len(v) for v in self._intent_history.values())
        }


conversation_memory = ConversationMemory()
