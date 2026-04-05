"""
记忆系统模块
基于SQLite的记忆存储和检索系统
"""

import sqlite3
import uuid
import time
import re
from typing import List, Dict, Optional

DB_PATH = "data.db"


def init_db():
    """
    初始化数据库
    创建 memories 和 reports 表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建 memories 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        user_message TEXT NOT NULL,
        agent_reply TEXT NOT NULL,
        agent TEXT NOT NULL,
        emotion_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建 reports 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        user_message TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")


def save_memory(user_message: str, agent_reply: str, agent: str, emotion_tag: Optional[str] = None) -> str:
    """
    存储对话记忆
    
    Args:
        user_message: 用户消息
        agent_reply: 智能体回复
        agent: 智能体名称
        emotion_tag: 情感标签
    
    Returns:
        记忆ID
    """
    memory_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO memories (id, user_message, agent_reply, agent, emotion_tag, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (memory_id, user_message, agent_reply, agent, emotion_tag, time.time())
    )
    
    conn.commit()
    conn.close()
    return memory_id


def get_recent_memories(limit: int = 3) -> List[Dict]:
    """
    获取最近的记忆
    
    Args:
        limit: 返回条数
    
    Returns:
        记忆列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_memories_by_emotion(emotion_tag: str) -> List[Dict]:
    """
    按情感标签检索记忆
    
    Args:
        emotion_tag: 情感标签
    
    Returns:
        记忆列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM memories WHERE emotion_tag = ? ORDER BY created_at DESC",
        (emotion_tag,)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_memory_by_keyword(keyword: str) -> List[Dict]:
    """
    简单关键词匹配检索记忆
    
    Args:
        keyword: 关键词
    
    Returns:
        匹配的记忆列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 简单的关键词匹配
    cursor.execute(
        "SELECT * FROM memories WHERE user_message LIKE ? OR agent_reply LIKE ? ORDER BY created_at DESC",
        (f"%{keyword}%", f"%{keyword}%")
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_memory_by_id(memory_id: str) -> Optional[Dict]:
    """
    根据ID获取记忆
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        记忆字典
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM memories WHERE id = ?",
        (memory_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_memory_count() -> int:
    """
    获取记忆总数
    
    Returns:
        记忆总数
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM memories")
    count = cursor.fetchone()[0]
    conn.close()
    
    return count
