"""
并行对话流 API
支持同时进行多个独立对话会话
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime
import logging

from ..auth import get_current_user
from ..database import get_db_connection
from ..services.consultant_agent import ConsultantAgent
from ..services.integral import IntegralService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consult/parallel", tags=["并行对话"])

CONSULT_INTEGRAL_COST = 1


class ParallelSessionCreate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None


class ParallelMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    session_id: str


class ParallelSession(BaseModel):
    id: str
    title: str
    topic: Optional[str]
    status: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    preview: Optional[str]


class ParallelSessionDetail(BaseModel):
    id: str
    title: str
    topic: Optional[str]
    status: str
    created_at: datetime
    last_message_at: datetime
    messages: List[Dict[str, Any]]
    profile: Optional[Dict[str, Any]] = None


class StreamResponse(BaseModel):
    session_id: str
    chunk: str
    is_final: bool
    full_response: Optional[str] = None


async def process_message_background(
    session_id: str,
    user_id: str,
    message: str,
    agent: ConsultantAgent
):
    try:
        result = await agent.process(message, session_id, user_id)
        
        conn = await get_db_connection()
        try:
            await conn.execute('''
                INSERT INTO consultation_history (id, user_id, session_id, role, content, intent, entities, created_at)
                VALUES (?, ?, ?, 'user', ?, NULL, NULL, ?)
            ''', (str(uuid.uuid4()), user_id, session_id, message, datetime.now()))
            
            await conn.execute('''
                INSERT INTO consultation_history (id, user_id, session_id, role, content, intent, entities, created_at)
                VALUES (?, ?, ?, 'assistant', ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), user_id, session_id, result['reply'], 
                  result.get('intent'), str(result.get('entities') or {}), datetime.now()))
            
            await conn.execute('''
                UPDATE consultation_sessions 
                SET updated_at = ?, title = COALESCE(title, ?)
                WHERE id = ?
            ''', (datetime.now(), message[:50] + '...' if len(message) > 50 else message, session_id))
            
            await conn.commit()
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Background message processing failed: {e}")


@router.post("/sessions", response_model=ParallelSession)
async def create_parallel_session(
    request: ParallelSessionCreate,
    user: dict = Depends(get_current_user)
):
    """创建新的并行对话会话"""
    user_id = user.get('id')
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    conn = await get_db_connection()
    try:
        await conn.execute('''
            INSERT INTO consultation_sessions (id, user_id, title, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?)
        ''', (session_id, user_id, request.title or f"新对话 {now.strftime('%H:%M')}", now, now))
        
        await conn.commit()
        
        return ParallelSession(
            id=session_id,
            title=request.title or f"新对话 {now.strftime('%H:%M')}",
            topic=request.topic,
            status='active',
            created_at=now,
            last_message_at=now,
            message_count=0,
            preview=None
        )
    finally:
        await conn.close()


@router.get("/sessions", response_model=List[ParallelSession])
async def list_parallel_sessions(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """获取用户的所有并行对话会话"""
    user_id = user.get('id')
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT 
                s.id, s.title, s.status, s.created_at, s.updated_at,
                (SELECT COUNT(*) FROM consultation_history h WHERE h.session_id = s.id) as message_count,
                (SELECT content FROM consultation_history h 
                 WHERE h.session_id = s.id 
                 ORDER BY h.created_at DESC LIMIT 1) as preview
            FROM consultation_sessions s
            WHERE s.user_id = ?
            ORDER BY s.updated_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = await cursor.fetchall()
        
        return [
            ParallelSession(
                id=row['id'],
                title=row['title'],
                topic=None,
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
                last_message_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at'],
                message_count=row['message_count'],
                preview=row['preview'][:100] if row['preview'] else None
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.get("/sessions/{session_id}", response_model=ParallelSessionDetail)
async def get_parallel_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """获取单个会话详情"""
    user_id = user.get('id')
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, user_id, title, status, created_at, updated_at
            FROM consultation_sessions
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        cursor = await conn.execute('''
            SELECT id, role, content, intent, entities, created_at
            FROM consultation_history
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,))
        
        messages = await cursor.fetchall()
        
        cursor = await conn.execute('''
            SELECT * FROM user_profiles WHERE user_id = ?
        ''', (user_id,))
        profile = await cursor.fetchone()
        
        return ParallelSessionDetail(
            id=session['id'],
            title=session['title'],
            topic=None,
            status=session['status'],
            created_at=datetime.fromisoformat(session['created_at']) if isinstance(session['created_at'], str) else session['created_at'],
            last_message_at=datetime.fromisoformat(session['updated_at']) if isinstance(session['updated_at'], str) else session['updated_at'],
            messages=[
                {
                    'id': msg['id'],
                    'role': msg['role'],
                    'content': msg['content'],
                    'intent': msg['intent'],
                    'created_at': msg['created_at']
                }
                for msg in messages
            ],
            profile=dict(profile) if profile else None
        )
    finally:
        await conn.close()


@router.post("/sessions/{session_id}/messages")
async def send_parallel_message(
    session_id: str,
    request: ParallelMessage,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """发送消息到指定会话（并行处理）"""
    user_id = user.get('id')
    
    success, error_msg, _ = await IntegralService.check_and_consume(
        user_id, 
        CONSULT_INTEGRAL_COST
    )
    
    if not success:
        raise HTTPException(
            status_code=402, 
            detail=f"积分不足，请充值后继续使用。{error_msg}"
        )
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id FROM consultation_sessions 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        agent = ConsultantAgent()
        result = await agent.process(request.content, session_id, user_id)
        
        await conn.execute('''
            INSERT INTO consultation_history (id, user_id, session_id, role, content, created_at)
            VALUES (?, ?, ?, 'user', ?, ?)
        ''', (str(uuid.uuid4()), user_id, session_id, request.content, datetime.now()))
        
        await conn.execute('''
            INSERT INTO consultation_history (id, user_id, session_id, role, content, intent, entities, created_at)
            VALUES (?, ?, ?, 'assistant', ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), user_id, session_id, result['reply'], 
              result.get('intent'), str(result.get('entities') or {}), datetime.now()))
        
        await conn.execute('''
            UPDATE consultation_sessions 
            SET updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), session_id))
        
        await conn.commit()
        
        return {
            'reply': result['reply'],
            'session_id': session_id,
            'action': result.get('action', 'done'),
            'intent': result.get('intent'),
            'entities': result.get('entities')
        }
        
    finally:
        await conn.close()


@router.delete("/sessions/{session_id}")
async def delete_parallel_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """删除会话"""
    user_id = user.get('id')
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id FROM consultation_sessions 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        await conn.execute(
            "DELETE FROM consultation_history WHERE session_id = ?", 
            (session_id,)
        )
        await conn.execute(
            "DELETE FROM consultation_sessions WHERE id = ?", 
            (session_id,)
        )
        await conn.commit()
        
        return {'success': True, 'message': '会话已删除'}
        
    finally:
        await conn.close()


@router.post("/sessions/{session_id}/clear")
async def clear_parallel_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """清空会话消息（保留会话）"""
    user_id = user.get('id')
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id FROM consultation_sessions 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        await conn.execute(
            "DELETE FROM consultation_history WHERE session_id = ?", 
            (session_id,)
        )
        await conn.commit()
        
        return {'success': True, 'message': '会话已清空'}
        
    finally:
        await conn.close()
