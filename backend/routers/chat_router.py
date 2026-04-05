"""
智能咨询对话API路由
支持32种场景的智能对话引导
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from backend.services.chat_guide_service import chat_guide_service

router = APIRouter(prefix="/api/chat", tags=["智能咨询"])


class OpeningRequest(BaseModel):
    personality: Optional[str] = Field(None, description="指定人格：周瑜 或 陆逊")


class ChatMessage(BaseModel):
    message: str = Field(..., description="用户消息")
    personality: Optional[str] = Field("周瑜", description="当前对话人格")
    session_id: Optional[str] = Field(None, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    personality: str
    message_count: int
    last_message: Optional[str] = None


sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/opening", summary="获取开场白")
async def get_opening(request: OpeningRequest):
    """
    获取平台开场白
    随机分配周瑜或陆逊人格
    """
    result = chat_guide_service.get_opening_message(request.personality)
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "session_id": session_id,
        "created_at": datetime.now(),
        "personality": result["personality"],
        "messages": [],
        "context": {}
    }
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            **result
        }
    }


@router.post("/message", summary="发送消息并获取回复")
async def send_message(request: ChatMessage):
    """
    发送用户消息，获取智能回复
    支持32种场景识别
    """
    session_id = request.session_id
    
    if session_id and session_id in sessions:
        session = sessions[session_id]
        personality = session.get("personality", request.personality)
        context = session.get("context", {})
    else:
        session_id = str(uuid.uuid4())
        personality = request.personality or "周瑜"
        context = request.context or {}
        sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "personality": personality,
            "messages": [],
            "context": context
        }
        session = sessions[session_id]
    
    result = chat_guide_service.generate_response(
        user_message=request.message,
        personality=personality,
        context=context
    )
    
    session["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    session["messages"].append({
        "role": "assistant",
        "content": result["response"],
        "timestamp": result["timestamp"]
    })
    session["context"]["last_category"] = result["category"]
    session["context"]["last_scene"] = result["scene"]
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "response": result["response"],
            "personality": result["personality"],
            "category": result["category"],
            "scene": result["scene"]
        }
    }


@router.get("/session/{session_id}", summary="获取会话信息")
async def get_session(session_id: str):
    """
    获取会话详情
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    
    return {
        "success": True,
        "data": {
            "session_id": session["session_id"],
            "created_at": session["created_at"],
            "personality": session["personality"],
            "message_count": len([m for m in session["messages"] if m["role"] == "user"]),
            "last_message": session["messages"][-1]["content"] if session["messages"] else None,
            "context": session["context"]
        }
    }


@router.get("/session/{session_id}/history", summary="获取会话历史")
async def get_session_history(session_id: str, limit: int = 20):
    """
    获取会话消息历史
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    messages = session["messages"][-limit:] if limit else session["messages"]
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "messages": messages,
            "total": len(session["messages"])
        }
    }


@router.delete("/session/{session_id}", summary="删除会话")
async def delete_session(session_id: str):
    """
    删除会话记录
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    del sessions[session_id]
    
    return {
        "success": True,
        "message": "会话已删除"
    }


@router.post("/session/{session_id}/context", summary="更新会话上下文")
async def update_context(session_id: str, context: Dict[str, Any]):
    """
    更新会话上下文信息
    可用于存储用户提供的出生信息、预算等
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    sessions[session_id]["context"].update(context)
    
    return {
        "success": True,
        "message": "上下文已更新",
        "context": sessions[session_id]["context"]
    }


@router.get("/scenes", summary="获取支持的场景列表")
async def get_scenes():
    """
    获取系统支持的所有对话场景
    """
    scenes = {
        "mingpan": [
            {"id": "mingpan_basic", "name": "命盘基础", "description": "用户想看命盘但不懂"},
            {"id": "time_unknown", "name": "时辰未知", "description": "用户不知道出生时辰"},
            {"id": "time_known", "name": "时辰已知", "description": "用户知道出生时辰"},
            {"id": "star_explain", "name": "星曜解释", "description": "用户询问特定星曜含义"},
            {"id": "wealth_star", "name": "财星分析", "description": "用户询问财运相关"},
            {"id": "marriage", "name": "婚姻分析", "description": "用户询问婚姻感情"},
            {"id": "city_direction", "name": "城市方向", "description": "用户询问适合发展的城市"},
            {"id": "wealth_bad", "name": "财运不佳", "description": "用户觉得财运不好"},
            {"id": "job_change", "name": "换工作", "description": "用户想换工作"},
            {"id": "career", "name": "行业选择", "description": "用户询问适合的行业"},
            {"id": "element", "name": "五行分析", "description": "用户询问五行方位"},
            {"id": "authority", "name": "权威分析", "description": "用户询问事业权威"}
        ],
        "property": [
            {"id": "property_sell", "name": "卖房咨询", "description": "用户想卖房"},
            {"id": "property_buy", "name": "买房咨询", "description": "用户想买房"},
            {"id": "property_school", "name": "学区房", "description": "用户想买学区房"},
            {"id": "property_new_old", "name": "新房二手房", "description": "用户纠结新房还是二手房"},
            {"id": "property_budget", "name": "预算咨询", "description": "用户有预算限制"},
            {"id": "property_payment", "name": "付款方式", "description": "用户纠结全款还是贷款"}
        ],
        "mixed": [
            {"id": "mixed_full", "name": "综合咨询", "description": "用户想看命盘选房"},
            {"id": "mixed_trust", "name": "信任确认", "description": "用户质疑准确性"}
        ],
        "chat": [
            {"id": "chat_casual", "name": "闲聊", "description": "用户随便看看"},
            {"id": "chat_skeptical", "name": "怀疑态度", "description": "用户表示不信"},
            {"id": "chat_cost", "name": "费用咨询", "description": "用户询问收费"},
            {"id": "chat_private", "name": "隐私顾虑", "description": "用户担心隐私"},
            {"id": "chat_ai_real", "name": "AI身份", "description": "用户询问是AI还是真人"},
            {"id": "chat_privacy", "name": "数据保存", "description": "用户询问数据保存"}
        ]
    }
    
    return {
        "success": True,
        "data": {
            "total_scenes": sum(len(v) for v in scenes.values()),
            "categories": scenes
        }
    }


@router.get("/personalities", summary="获取人格列表")
async def get_personalities():
    """
    获取支持的对话人格
    """
    return {
        "success": True,
        "data": {
            "personalities": [
                {
                    "id": "周瑜",
                    "name": "周瑜",
                    "style": "豪爽直接",
                    "description": "热情开朗，说话直接，喜欢用比喻和幽默"
                },
                {
                    "id": "陆逊",
                    "name": "陆逊",
                    "style": "稳重细腻",
                    "description": "温和理性，说话细腻，注重逻辑和细节"
                }
            ]
        }
    }


@router.post("/detect-intent", summary="检测用户意图")
async def detect_intent(message: str):
    """
    检测用户消息的意图类别
    """
    category, scene = chat_guide_service.detect_intent(message)
    
    return {
        "success": True,
        "data": {
            "message": message,
            "category": category,
            "scene": scene
        }
    }
