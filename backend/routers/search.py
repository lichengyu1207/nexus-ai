"""
全局搜索API路由
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import SearchDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str
    type: str
    title: str
    snippet: str
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[SearchResult]
    total: int
    query: str


class SuggestionResult(BaseModel):
    """搜索建议模型"""
    id: str
    type: str
    title: str


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    type: Optional[str] = Query(None, description="类型过滤，逗号分隔"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    全局搜索
    
    Args:
        q: 搜索关键词
        type: 类型过滤
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        SearchResponse: 搜索结果
    """
    types = None
    if type:
        types = [t.strip() for t in type.split(",") if t.strip() in ["task", "report"]]
    
    results, total = await SearchDB.search(
        query=q,
        user_id=current_user["id"],
        types=types,
        limit=limit,
        offset=offset
    )
    
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        total=total,
        query=q
    )


@router.get("/suggestions", response_model=List[SuggestionResult])
async def get_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=10),
    current_user: dict = Depends(get_current_user)
):
    """
    获取搜索建议
    
    Args:
        q: 搜索关键词
        limit: 返回数量
        current_user: 当前用户
        
    Returns:
        List[SuggestionResult]: 搜索建议列表
    """
    suggestions = await SearchDB.get_suggestions(
        query=q,
        user_id=current_user["id"],
        limit=limit
    )
    
    return [SuggestionResult(**s) for s in suggestions]
