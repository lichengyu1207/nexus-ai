"""
辩论API端点
提供辩论记录的查询和触发功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.ai_agents.debate import debate_manager


router = APIRouter()


# ========== Pydantic模型 ==========

class DebateTurnResponse(BaseModel):
    """辩论回合响应模型"""
    id: str = Field(..., description="回合ID")
    session_id: str = Field(..., description="会话ID")
    agent_name: str = Field(..., description="代理名称")
    content: str = Field(..., description="发言内容")
    turn_number: int = Field(..., description="回合编号")
    created_at: str = Field(..., description="创建时间")


class DebateSessionResponse(BaseModel):
    """辩论会话响应模型"""
    id: str = Field(..., description="会话ID")
    task_id: str = Field(..., description="任务ID")
    topic: str = Field(..., description="辩论主题")
    participants: List[str] = Field(..., description="参与者列表")
    turns: List[DebateTurnResponse] = Field(..., description="辩论回合列表")
    started_at: str = Field(..., description="开始时间")
    ended_at: Optional[str] = Field(None, description="结束时间")
    status: str = Field(..., description="状态")
    current_turn: int = Field(..., description="当前回合数")
    max_turns: int = Field(..., description="最大回合数")


class DebateCreate(BaseModel):
    """创建辩论请求模型"""
    topic: str = Field(..., description="辩论主题")
    participants: List[str] = Field(..., description="参与者列表")
    description: Optional[str] = Field(None, description="辩论描述")


class DebateTurnCreate(BaseModel):
    """添加辩论回合请求模型"""
    agent_name: str = Field(..., description="代理名称")
    content: str = Field(..., description="发言内容")


# ========== API端点 ==========

@router.get("/tasks/{task_id}/debate", response_model=List[DebateSessionResponse])
async def get_task_debates(task_id: str):
    """
    获取任务的所有辩论记录
    
    Args:
        task_id: 任务ID
        
    Returns:
        List[DebateSessionResponse]: 辩论会话列表
    """
    try:
        transcripts = debate_manager.get_all_transcripts(task_id)
        
        sessions = []
        for transcript in transcripts:
            turns = [
                DebateTurnResponse(**turn)
                for turn in transcript.get("turns", [])
            ]
            
            session = DebateSessionResponse(
                id=transcript["id"],
                task_id=transcript["task_id"],
                topic=transcript["topic"],
                participants=transcript["participants"],
                turns=turns,
                started_at=transcript["started_at"],
                ended_at=transcript.get("ended_at"),
                status=transcript["status"],
                current_turn=transcript["current_turn"],
                max_turns=transcript["max_turns"]
            )
            sessions.append(session)
        
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debate/{session_id}", response_model=DebateSessionResponse)
async def get_debate_session(session_id: str):
    """
    获取特定辩论会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        DebateSessionResponse: 辩论会话
    """
    try:
        transcript = debate_manager.get_transcript(session_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        turns = [
            DebateTurnResponse(**turn)
            for turn in transcript.get("turns", [])
        ]
        
        return DebateSessionResponse(
            id=transcript["id"],
            task_id=transcript["task_id"],
            topic=transcript["topic"],
            participants=transcript["participants"],
            turns=turns,
            started_at=transcript["started_at"],
            ended_at=transcript.get("ended_at"),
            status=transcript["status"],
            current_turn=transcript["current_turn"],
            max_turns=transcript["max_turns"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/debate", response_model=DebateSessionResponse)
async def create_debate(task_id: str, debate: DebateCreate):
    """
    手动触发辩论（调试用）
    
    Args:
        task_id: 任务ID
        debate: 辩论创建请求
        
    Returns:
        DebateSessionResponse: 创建的辩论会话
    """
    try:
        session = debate_manager.start_debate(
            task_id=task_id,
            topic=debate.topic,
            participants=debate.participants
        )
        
        return DebateSessionResponse(
            id=session.id,
            task_id=session.task_id,
            topic=session.topic,
            participants=session.participants,
            turns=[],
            started_at=session.started_at.isoformat(),
            ended_at=None,
            status=session.status,
            current_turn=0,
            max_turns=session.max_turns
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate/{session_id}/turn", response_model=DebateTurnResponse)
async def add_debate_turn(session_id: str, turn: DebateTurnCreate):
    """
    添加辩论发言
    
    Args:
        session_id: 会话ID
        turn: 辩论回合创建请求
        
    Returns:
        DebateTurnResponse: 创建的辩论回合
    """
    try:
        debate_turn = debate_manager.add_turn(
            session_id=session_id,
            agent_name=turn.agent_name,
            content=turn.content
        )
        
        if not debate_turn:
            raise HTTPException(status_code=400, detail="Failed to add debate turn")
        
        return DebateTurnResponse(
            id=debate_turn.id,
            session_id=debate_turn.session_id,
            agent_name=debate_turn.agent_name,
            content=debate_turn.content,
            turn_number=debate_turn.turn_number,
            created_at=debate_turn.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate/{session_id}/end")
async def end_debate(session_id: str):
    """
    结束辩论
    
    Args:
        session_id: 会话ID
        
    Returns:
        dict: 操作结果
    """
    try:
        success = debate_manager.end_debate(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        return {
            "session_id": session_id,
            "message": "Debate ended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
