"""
命盘解读咨询API路由
提供用户与平台的交互接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.mingpan_reading_service import mingpan_reading_service

router = APIRouter(prefix="/api/reading", tags=["reading"])

_reading_sessions: Dict[str, List[Dict]] = {}


class ReadingRequest(BaseModel):
    """解读请求"""
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class ReadingResponse(BaseModel):
    """解读响应"""
    intent: str
    opening: str
    dimensions: Dict[str, str]
    summary: str
    next_steps: List[str]
    similar_cases: List[Dict[str, Any]]
    timestamp: str


class QuickAnalysisRequest(BaseModel):
    """快速分析请求"""
    age: int
    gender: str
    current_situation: str
    main_question: str


class QuickAnalysisResponse(BaseModel):
    """快速分析响应"""
    pattern_type: str
    wealth_type: str
    career_stage: str
    key_advice: str
    laohai_comment: str


@router.post("/analyze", response_model=ReadingResponse)
async def analyze_reading(request: ReadingRequest):
    """
    分析用户问题，    Args:
        request: 解读请求
        
    Returns:
        ReadingResponse: 解读结果
    """
    result = mingpan_reading_service.analyze_user_query(
        query=request.query,
        user_context=request.context
    )
    
    similar_cases = _find_similar_cases(result.get("key_info", {}))
    
    session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if session_id not in _reading_sessions:
        _reading_sessions[session_id] = []
    _reading_sessions[session_id].append({
        "query": request.query,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    
    return ReadingResponse(
        intent=result.get("intent", "整体分析"),
        opening=result.get("personalized_output", {}).get("opening", ""),
        dimensions=result.get("personalized_output", {}).get("dimensions", {}),
        summary=result.get("personalized_output", {}).get("summary", ""),
        next_steps=result.get("personalized_output", {}).get("next_steps", []),
        similar_cases=similar_cases,
        timestamp=datetime.now().isoformat()
    )


@router.post("/quick", response_model=QuickAnalysisResponse)
async def quick_analysis(request: QuickAnalysisRequest):
    """
    快速分析
    
    Args:
        request: 快速分析请求
        
    Returns:
        QuickAnalysisResponse: 快速分析结果
    """
    age = request.age
    if age < 30:
        career_stage = "30岁前-试错期"
    elif age < 40:
        career_stage = "30岁后-扎根期"
    else:
        career_stage = "40岁后-做局期"
    
    situation = request.current_situation.lower()
    
    if any(kw in situation for kw in ["创业", "做生意", "老板"]):
        pattern_type = "龙尊型/蛇灵型"
        wealth_type = "偏财型"
        key_advice = "创业需要耐心，蛇灵型的人要等时机，龙尊型的人要会用人"
    elif any(kw in situation for kw in ["体制内", "公务员", "国企"]):
        pattern_type = "鹤贤型"
        wealth_type = "正财型"
        key_advice = "稳扎稳打，靠积累上升，别想一夜暴富"
    elif any(kw in situation for kw in ["销售", "市场", "人脉"]):
        pattern_type = "凤仪型"
        wealth_type = "偏财型"
        key_advice = "圈子是你的资产，维护好人脉网络"
    else:
        pattern_type = "混合型"
        wealth_type = "正财型"
        key_advice = "先确定自己的天赋方向，再选择适合的赛道"
    
    laohai_comment = _generate_laohai_quick_comment(
        pattern_type, wealth_type, career_stage, request.main_question
    )
    
    return QuickAnalysisResponse(
        pattern_type=pattern_type,
        wealth_type=wealth_type,
        career_stage=career_stage,
        key_advice=key_advice,
        laohai_comment=laohai_comment
    )


@router.get("/session/{session_id}")
async def get_session_history(session_id: str):
    """获取会话历史"""
    if session_id not in _reading_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "session_id": session_id,
        "history": _reading_sessions[session_id],
        "total_interactions": len(_reading_sessions[session_id])
    }


@router.get("/dimensions")
async def get_dimension_guide():
    """获取六维框架指南"""
    return {
        "dimensions": [
            {
                "name": "格局定基调",
                "description": "你的天赋赛道在哪",
                "types": ["凤仪型", "蛇灵型", "鹤贤型", "龙尊型"],
                "key_question": "做什么事最顺、最来劲？"
            },
            {
                "name": "财运通道",
                "description": "你的钱从哪来",
                "types": ["正财型", "偏财型"],
                "key_question": "你是靠积累还是靠机会？"
            },
            {
                "name": "姻缘逻辑",
                "description": "你是谁，才遇到谁",
                "types": ["高段位", "中段位", "低段位"],
                "key_question": "你的段位匹配什么样的人？"
            },
            {
                "name": "事业路径",
                "description": "什么时候该干什么",
                "types": ["30岁前试错期", "30岁后扎根期", "40岁后做局期"],
                "key_question": "你现在在哪个节点？"
            },
            {
                "name": "人际过滤",
                "description": "谁是滋养，谁是消耗",
                "types": ["滋养型", "消耗型"],
                "key_question": "身边的人给你空间还是限制你？"
            },
            {
                "name": "执行力心态",
                "description": "能不能把盘变成现实",
                "types": ["强", "中", "弱"],
                "key_question": "你看得懂，做得到吗？"
            }
        ],
        "core_philosophy": "命盘不是判官，是地图。地图再好，也得有人走。"
    }


@router.get("/examples")
async def get_example_queries():
    """获取示例问题"""
    return {
        "examples": [
            {
                "category": "财运分析",
                "query": "我什么时候能发财？",
                "better_query": "我是正财还是偏财？我的钱应该从哪来？"
            },
            {
                "category": "姻缘分析",
                "query": "我什么时候能结婚？",
                "better_query": "我现在处于什么段位？我该匹配什么样的人？"
            },
            {
                "category": "事业分析",
                "query": "我该入什么行业？",
                "better_query": "我现在在哪个节点？下一步该怎么走？"
            },
            {
                "category": "天赋分析",
                "query": "我有什么天赋？",
                "better_query": "我做什么事最顺、最来劲？我的天赋赛道在哪？"
            },
            {
                "category": "人际分析",
                "query": "我身边的人为什么总是拖累我？",
                "better_query": "我身边的人是滋养型还是消耗型？怎么保护自己的能量场？"
            }
        ],
        "tip": "问对问题，才能得到有用的答案。"
    }


def _find_similar_cases(key_info: Dict) -> List[Dict]:
    """查找相似案例"""
    from ..models.mingpan_case import SAMPLE_CASES
    
    similar = []
    for case in SAMPLE_CASES[:3]:
        similar.append({
            "case_id": case.get("case_id"),
            "name": case.get("anonymized_name"),
            "pattern": case.get("dimension_1_pattern", {}).get("type"),
            "outcome": case.get("outcome_status"),
            "key_lesson": case.get("outcome_lessons", [""])[0] if case.get("outcome_lessons") else ""
        })
    return similar


def _generate_laohai_quick_comment(pattern: str, wealth: str, stage: str, question: str) -> str:
    """生成老骇快速点评"""
    comment = f"你是{pattern}，{wealth}。"
    
    if "试错期" in stage:
        comment += "你现在在试错期，可以多尝试，但每次换都要往更高阶跳。"
    elif "扎根期" in stage:
        comment += "你到了扎根期，选一个赛道，深耕下去。"
    else:
        comment += "你到了做局期，从做事变成做人，培养接班人。"
    
    comment += f"关于你的问题'{question}'，记住：命盘是地图，你得自己走。"
    
    return comment
