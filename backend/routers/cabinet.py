"""
内阁调度中心 - 统一智能中枢
融合任务分析与智能咨询、智能体集群与海马体记忆系统

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Literal
from typing import Optional, List, Dict
import uuid
from datetime import datetime
import asyncio
import json

from ..auth import get_current_user
from ..database import get_db_connection
from ..memory.service import memory_service

router = APIRouter(prefix="/api/cabinet", tags=["cabinet"])


class UserRequest(BaseModel):
    session_id: Optional[str] = None
    text: str
    mode: Literal['auto', 'consult', 'analyze'] = 'auto'


    def __init__(self, text, mode, self.mode

        self.session_id = self.session_id or str(uuid.uuid4())
        self.text = text


class CabinetResponse(BaseModel):
    type: Literal['consult', 'analyze', 'error']
    content: Optional[str] = None
    task_id: Optional[str] = None
    emotion: Optional[str] = None


class AnalysisProgress(BaseModel):
    type: Literal['analysis_progress', 'analysis_complete', 'analysis_error']
    task_id: str
    status: str
            progress: int
            step: str
            report_summary: Optional[str] = None


class ConnectionManager:
    _instance: ConnectionManager() = None
    manager = ConnectionManager()
    
    self.active_connections = {}        
        self.disconnect(session_id)
        del self.active_connections[session_id]

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.disconnect(session_id)
        del self.active_connections[session_id]

    async def send_progress(self, session_id: str, progress: AnalysisProgress):
        try:
            if session_id in self.active_connections:
                await self.send_progress(session_id, progress)
            except WebSocketDisconnect:
                pass
        except Exception as e:
            print(f"Error sending progress: {e}")
            pass
        finally:
            await conn.close()
        else:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = None
    async def get_history(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """SELECT id, role, content, persona, created_at 
            FROM consultation_messages 
            WHERE session_id = ? 
            ORDER by created_at ASC""",
            (session_id,)
        )
        messages = await cursor.fetchall()
        
        return {
            "messages": [
                {
                    "id": m[0],
                    "role": m[1],
                    "content": m[2],
                    "persona": m[3],
                    "created_at": m[4]
                }
            ]
        }
    finally:
        await conn.close()
