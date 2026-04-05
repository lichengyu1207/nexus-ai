#!/usr/bin/env python3
"""
人格风格对话API
"""

import json
import os
import sys
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.conversation.dialogue_system import DialogueSystem
from backend.personality.personality_library import Personality

# 初始化FastAPI应用
app = FastAPI(title="人格风格对话API", description="提供基于历史人物风格的对话服务")

# 初始化对话系统
dialogue_system = DialogueSystem()

# 定义请求模型
class ChatRequest(BaseModel):
    user_input: str
    personality_name: Optional[str] = None

class RatingRequest(BaseModel):
    personality_name: str
    satisfaction: float
    style_ratings: Optional[Dict[str, float]] = None

class CustomPersonalityRequest(BaseModel):
    personality_id: str
    name: str
    era: str
    source: str
    personality_dimensions: Dict[str, float]
    language_style: Dict[str, Any]
    knowledge_domains: List[str]
    emotional_templates: Dict[str, List[str]]
    metadata: Optional[Dict[str, Any]] = None

# 定义响应模型
class ChatResponse(BaseModel):
    response: str
    personality_name: str
    emotion: str
    intent: str

class PersonalitiesResponse(BaseModel):
    personalities: List[str]

class PersonalityDetailsResponse(BaseModel):
    personality: Dict[str, Any]

# API端点
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """进行对话"""
    try:
        response = dialogue_system.process(request.user_input, request.personality_name)
        # 这里简化处理，实际应用中需要从对话系统获取情绪和意图
        emotion = "消极" if "压力" in request.user_input else "中性"
        intent = "倾诉" if "压力" in request.user_input else "其他"
        personality_name = request.personality_name or "周瑜"
        return ChatResponse(
            response=response,
            personality_name=personality_name,
            emotion=emotion,
            intent=intent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rate")
async def rate(request: RatingRequest):
    """对回复进行评分"""
    try:
        dialogue_system.system_evolution.record_satisfaction(
            request.personality_name,
            request.satisfaction,
            request.style_ratings
        )
        dialogue_system.system_evolution.evolve(request.personality_name)
        return {"message": "评分记录成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/personalities", response_model=PersonalitiesResponse)
async def get_personalities():
    """获取可用的人格列表"""
    try:
        personalities = dialogue_system.list_available_personalities()
        return PersonalitiesResponse(personalities=personalities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/personalities/{name}", response_model=PersonalityDetailsResponse)
async def get_personality_details(name: str):
    """获取人格详细信息"""
    try:
        personality = dialogue_system.get_personality_details(name)
        if not personality:
            raise HTTPException(status_code=404, detail="人格不存在")
        return PersonalityDetailsResponse(personality=personality.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/personalities")
async def add_custom_personality(request: CustomPersonalityRequest):
    """添加自定义人格"""
    try:
        personality = Personality(
            personality_id=request.personality_id,
            name=request.name,
            era=request.era,
            source=request.source,
            personality_dimensions=request.personality_dimensions,
            language_style=request.language_style,
            knowledge_domains=request.knowledge_domains,
            emotional_templates=request.emotional_templates,
            metadata=request.metadata or {}
        )
        dialogue_system.add_custom_personality(personality)
        return {"message": "自定义人格添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 运行应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
