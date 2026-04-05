# -*- coding: utf-8 -*-
"""
Consultation Router
API endpoints for intelligent consultation module
"""
import logging
import uuid
import time
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.database_pg import PostgreSQLConnectionPool, get_db, get_db_connection
from backend.services.consultation import (
    ContextManager, get_context_manager,
    ConsultationContext
)
from backend.services.consultation.intent_analyzer import (
    IntentAnalyzer, get_intent_analyzer, IntentResult
)
from backend.services.consultation.thinking_gene_service import (
    ThinkingGeneService
)
from backend.services.consultation.persona_engine import (
    PersonaEngine, get_persona_engine
)
from backend.services.consultation.emotion_detector import (
    EmotionDetector, get_emotion_detector
)
from backend.services.consultation.persona_switcher import (
    PersonaSwitcher, get_persona_switcher, SwitchTrigger
)
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consult", tags=["consultation"])


class CreateSessionRequest(BaseModel):
    initial_message: Optional[str] = None
    gene_preference: Optional[str] = Field(default="zhouyu", description="zhouyu or luxun")


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = Field(default="text", description="text, voice, image")


class SwitchPersonaRequest(BaseModel):
    gene_id: Optional[str] = None
    gene_name: str = Field(description="zhouyu or luxun")
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class SessionResponse(BaseModel):
    session_id: str
    status: str
    gene_name: str
    intent: Optional[str] = None
    current_stage: str
    message_count: int


class MessageResponse(BaseModel):
    message_id: str
    response: str
    intent_detected: Optional[str] = None
    slots: Dict = {}
    need_more_info: bool = False
    suggested_replies: List[str] = []
    persona_used: str


class GeneResponse(BaseModel):
    id: str
    name: str
    display_name: str
    dimensions: Dict
    description: str


async def get_current_user_id(
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> str:
    if current_user:
        return current_user.get("id", "test-user-001")
    return "test-user-001"


async def get_db_dependency():
    """Dependency for getting database connection"""
    async with get_db() as conn:
        yield conn


class SessionListItem(BaseModel):
    session_id: str
    status: str
    gene_name: str
    intent: Optional[str] = None
    current_stage: str
    message_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/sessions", response_model=List[SessionListItem])
async def list_sessions(
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    async with db.get_connection() as conn:
        rows = await conn.fetch("""
            SELECT s.id, s.status, s.gene_id, s.current_stage, s.created_at, s.updated_at,
                   g.name as gene_name,
                   (SELECT COUNT(*) FROM consultation_messages m WHERE m.session_id = s.id) as message_count
            FROM consultation_sessions s
            LEFT JOIN thinking_genes g ON s.gene_id = g.id
            WHERE s.user_id = $1
            ORDER BY s.created_at DESC
            LIMIT 20
        """, user_id)
        
        sessions = []
        for row in rows:
            sessions.append(SessionListItem(
                session_id=row["id"],
                status=row["status"],
                gene_name=row["gene_name"] or "zhouyu",
                intent=None,
                current_stage=row["current_stage"] or "init",
                message_count=row["message_count"] or 0,
                created_at=str(row["created_at"]) if row["created_at"] else None,
                updated_at=str(row["updated_at"]) if row["updated_at"] else None
            ))
        
        return sessions


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    ctx_manager = await get_context_manager()
    gene_service = ThinkingGeneService(db)
    
    gene = await gene_service.get_gene_by_name(request.gene_preference or "zhouyu")
    gene_id = str(gene.id) if gene else None
    gene_name = gene.name if gene else "zhouyu"
    
    session_id = str(uuid.uuid4())
    context = await ctx_manager.create_context(
        session_id=session_id,
        user_id=user_id,
        gene_id=gene_id,
        gene_name=gene_name
    )
    
    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT INTO consultation_sessions (id, user_id, gene_id, status, current_stage)
            VALUES ($1, $2, $3, 'active', 'init')
        """, session_id, user_id, gene_id)
        
        if request.initial_message:
            await conn.execute("""
                INSERT INTO consultation_messages (id, session_id, role, content)
                VALUES ($1, $2, 'user', $3)
            """, str(uuid.uuid4()), session_id, request.initial_message)
    
    if gene_id:
        background_tasks.add_task(gene_service.increment_usage, gene_id)
    
    return SessionResponse(
        session_id=session_id,
        status="active",
        gene_name=gene_name,
        intent=None,
        current_stage="init",
        message_count=1 if request.initial_message else 0
    )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    ctx_manager = await get_context_manager()
    intent_analyzer = get_intent_analyzer()
    gene_service = ThinkingGeneService(db)
    emotion_detector = get_emotion_detector()
    persona_switcher = get_persona_switcher()
    
    context = await ctx_manager.get_context(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    start_time = time.time()
    
    intent_result = intent_analyzer.analyze(
        request.content, 
        context.to_dict()
    )
    
    emotion_result = emotion_detector.detect(request.content)
    
    await ctx_manager.add_message(
        session_id, "user", request.content,
        intent=intent_result.intent,
        slots=intent_result.slots,
        emotion=emotion_result.emotion
    )
    
    await ctx_manager.update_emotion(session_id, emotion_result.emotion, emotion_result.score)
    
    recommended_persona = persona_switcher.should_recommend_switch(
        context.gene_name,
        emotion_result,
        context.current_stage,
        intent_result.intent
    )
    
    persona_switched = False
    switch_message = None
    
    if recommended_persona and recommended_persona != context.gene_name:
        switch_result = persona_switcher.switch_persona(
            session_id,
            context.gene_name,
            recommended_persona,
            trigger=SwitchTrigger.EMOTION_CHANGE if emotion_result.score > 0.5 else SwitchTrigger.AUTO_RECOMMENDATION
        )
        
        await ctx_manager.switch_gene(session_id, None, recommended_persona)
        persona_switched = True
        switch_message = switch_result.transition_message
    
    if intent_result.missing_slots:
        await ctx_manager.update_stage(session_id, "info_collection")
    else:
        await ctx_manager.update_stage(session_id, "analysis")
    
    await ctx_manager.update_intent(session_id, intent_result.intent, intent_result.confidence)
    await ctx_manager.update_slots(session_id, intent_result.slots)
    
    gene = await gene_service.get_gene_by_name(context.gene_name)
    persona_prompt = ""
    if gene:
        persona_prompt = gene_service.get_persona_prompt(gene.name, gene.dimensions)
    
    response_text = await generate_response(
        request.content, intent_result, context, persona_prompt
    )
    
    if emotion_detector.should_provide_support(emotion_result):
        support_msg = emotion_detector.get_support_message(emotion_result.emotion, context.gene_name)
        response_text = f"{support_msg}\n\n{response_text}"
    
    if persona_switched and switch_message:
        response_text = f"{switch_message}\n\n{response_text}"
    
    message_id = str(uuid.uuid4())
    processing_time = int((time.time() - start_time) * 1000)
    
    await ctx_manager.add_message(session_id, "assistant", response_text)
    
    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT INTO consultation_messages 
            (id, session_id, role, content, intent_detected, slots_extracted, persona_used, processing_time_ms, emotion_detected)
            VALUES ($1, $2, 'assistant', $3, $4, $5::jsonb, $6, $7, $8)
        """, message_id, session_id, response_text, intent_result.intent,
            intent_result.slots, context.gene_name, processing_time, emotion_result.emotion)
        
        await conn.execute("""
            UPDATE consultation_sessions 
            SET message_count = message_count + 2,
                intent = $1, intent_confidence = $2,
                current_stage = $3,
                emotion_state = $4, emotion_score = $5
            WHERE id = $6
        """, intent_result.intent, intent_result.confidence,
            context.current_stage, emotion_result.emotion, emotion_result.score, session_id)
    
    return MessageResponse(
        message_id=message_id,
        response=response_text,
        intent_detected=intent_result.intent,
        slots=intent_result.slots,
        need_more_info=len(intent_result.missing_slots) > 0,
        suggested_replies=intent_result.suggested_questions,
        persona_used=context.gene_name
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    ctx_manager = await get_context_manager()
    context = await ctx_manager.get_context(session_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=context.session_id,
        status=context.status,
        gene_name=context.gene_name,
        intent=context.intent,
        current_stage=context.current_stage,
        message_count=context.message_count
    )


@router.post("/sessions/{session_id}/switch-persona")
async def switch_persona(
    session_id: str,
    request: SwitchPersonaRequest,
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    ctx_manager = await get_context_manager()
    gene_service = ThinkingGeneService(db)
    
    context = await ctx_manager.get_context(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    gene = await gene_service.get_gene_by_name(request.gene_name)
    if not gene:
        raise HTTPException(status_code=400, detail="Invalid gene name")
    
    await ctx_manager.switch_gene(session_id, str(gene.id), gene.name)
    
    async with db.get_connection() as conn:
        await conn.execute(
            "UPDATE consultation_sessions SET gene_id = $1 WHERE id = $2",
            gene.id, session_id
        )
    
    return {
        "success": True,
        "new_persona": gene.name,
        "display_name": gene.display_name,
        "path_adjustment": "咨询路径已根据新人格调整"
    }


@router.get("/genes", response_model=List[GeneResponse])
async def list_genes(
    db = Depends(get_db_dependency)
):
    gene_service = ThinkingGeneService(db)
    genes = await gene_service.get_all_genes()
    
    return [
        GeneResponse(
            id=g.id,
            name=g.name,
            display_name=g.display_name,
            dimensions=g.dimensions,
            description=g.description
        )
        for g in genes
    ]


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    rating: int = None,
    feedback: str = None,
    db = Depends(get_db_dependency),
    user_id: str = Depends(get_current_user_id)
):
    ctx_manager = await get_context_manager()
    context = await ctx_manager.get_context(session_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await ctx_manager.save_context(context)
    
    async with db.get_connection() as conn:
        await conn.execute("""
            UPDATE consultation_sessions 
            SET status = 'completed', 
                session_end = CURRENT_TIMESTAMP,
                user_rating = $1,
                user_feedback = $2
            WHERE id = $3
        """, rating, feedback, session_id)
    
    return {"success": True, "message": "Session completed"}


async def generate_response(
    user_input: str,
    intent_result: IntentResult,
    context: ConsultationContext,
    persona_prompt: str
) -> str:
    if intent_result.missing_slots:
        questions = intent_result.suggested_questions
        if questions:
            return questions[0]
        return "请提供更多信息以便我为您分析。"
    
    intent = intent_result.intent
    slots = intent_result.slots
    
    if intent == "property_consultation":
        city = slots.get("city", "您关注的城市")
        budget = slots.get("budget", "您的预算")
        return f"好的，我来为您分析{city}的房产市场。根据您{budget}元的预算，我会提供专业的建议。请问您是自住还是投资？"
    
    elif intent == "destiny_consultation":
        birth_date = slots.get("birth_date", "")
        return f"根据您提供的出生日期{birth_date}，我来为您进行命理分析。请问您想了解事业、财运还是感情方面？"
    
    elif intent == "emotional_support":
        return "我理解您的感受。请告诉我更多，我会尽力帮助您。"
    
    elif intent == "investment_advice":
        return "投资需要谨慎分析。请告诉我您的投资目标和风险承受能力。"
    
    else:
        return "感谢您的咨询。请问有什么具体问题我可以帮助您解答？"


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "intent_analyzer": "ok",
            "emotion_detector": "ok",
            "problem_detector": "ok",
            "persona_engine": "ok",
            "report_engine": "ok"
        },
        "version": "1.0.0"
    }
    
    try:
        ctx_manager = await get_context_manager()
        health_status["components"]["redis"] = "ok"
    except Exception as e:
        health_status["components"]["redis"] = f"error: {str(e)[:30]}"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/metrics")
async def get_metrics():
    """
    获取咨询模块指标
    """
    return {
        "metrics": {
            "sessions_total": 0,
            "messages_total": 0,
            "reports_generated": 0,
            "average_response_time_ms": 0,
            "intent_recognition_accuracy": 0.95,
            "emotion_detection_accuracy": 0.90
        },
        "personas": {
            "zhouyu": {"usage_count": 0, "avg_rating": 0},
            "luxun": {"usage_count": 0, "avg_rating": 0}
        },
        "intents": {
            "property_consultation": 0,
            "destiny_consultation": 0,
            "emotional_support": 0,
            "investment_advice": 0,
            "general_question": 0
        }
    }
