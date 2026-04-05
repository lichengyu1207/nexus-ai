"""
管理员吉祥物管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.auth import get_current_user, require_admin
from backend.database import get_db
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/mascot", tags=["admin-mascot"])


class MascotEmotion(BaseModel):
    """吉祥物表情模型"""
    id: str
    name: str
    emotion: str
    pose: Optional[str] = None
    svg_path: str
    created_at: str


class MascotQuote(BaseModel):
    """吉祥物语录模型"""
    id: str
    text: str
    category: str
    created_at: str


class MascotQuoteCreate(BaseModel):
    """创建语录请求"""
    text: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="random")


class MascotQuoteUpdate(BaseModel):
    """更新语录请求"""
    text: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None


class MascotStats(BaseModel):
    """吉祥物统计"""
    total_clicks: int
    total_drag_events: int
    total_scene_triggers: int
    clicks_today: int
    popular_scenes: List[dict]
    recent_interactions: List[dict]


@router.get("/emotions")
async def get_emotions(
    current_user: dict = Depends(require_admin)
):
    """获取所有表情"""
    emotions = [
        {"id": "1", "name": "默认", "emotion": "default", "svg_path": "/images/mascot/expressions/default.svg"},
        {"id": "2", "name": "思考", "emotion": "thinking", "svg_path": "/images/mascot/expressions/thinking.svg"},
        {"id": "3", "name": "开心", "emotion": "happy", "svg_path": "/images/mascot/expressions/happy.svg"},
        {"id": "4", "name": "困惑", "emotion": "confused", "svg_path": "/images/mascot/expressions/confused.svg"},
        {"id": "5", "name": "惊讶", "emotion": "surprised", "svg_path": "/images/mascot/expressions/surprised.svg"},
        {"id": "6", "name": "安慰", "emotion": "comforting", "svg_path": "/images/mascot/expressions/reassuring.svg"},
    ]
    return {"emotions": emotions}


@router.get("/quotes")
async def get_quotes(
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """获取所有语录"""
    quotes = [
        # 常见语录
        {"id": "1", "text": "今天天气不错，适合看房～", "category": "default", "created_at": "2024-01-01T00:00:00"},
        {"id": "2", "text": "数据分析中，请勿打扰～", "category": "thinking", "created_at": "2024-01-01T00:00:00"},
        {"id": "3", "text": "太棒了！分析完成啦～", "category": "happy", "created_at": "2024-01-01T00:00:00"},
        {"id": "4", "text": "恭喜你发现了彩蛋！🎉", "category": "easterEgg", "created_at": "2024-01-01T00:00:00"},
        {"id": "5", "text": "你知道吗？房产投资最重要的是地段～", "category": "random", "created_at": "2024-01-01T00:00:00"},
        {"id": "6", "text": "欢迎来到房产分析平台，有什么可以帮您的吗？", "category": "welcome", "created_at": "2024-01-01T00:00:00"},
        {"id": "7", "text": "正在努力加载中，请稍等片刻～", "category": "loading", "created_at": "2024-01-01T00:00:00"},
        {"id": "8", "text": "任务已完成，干得漂亮！", "category": "success", "created_at": "2024-01-01T00:00:00"},
        {"id": "9", "text": "哎呀，出了点小问题，让我想想办法～", "category": "error", "created_at": "2024-01-01T00:00:00"},
        {"id": "10", "text": "记得保存您的工作哦～", "category": "reminder", "created_at": "2024-01-01T00:00:00"},
        
        # 搞怪语录
        {"id": "11", "text": "我不是在摸鱼，我是在思考人生～", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "12", "text": "这个需求有点难，让我先喝口水压压惊", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "13", "text": "打工人的快乐就是这么朴实无华～", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "14", "text": "今天也是元气满满的一天呢！（大概）", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "15", "text": "我不是胖，我只是毛茸茸的～", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "16", "text": "别点了别点了，再点我就要晕了～", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "17", "text": "这个功能...我还在开发中（其实还没开始）", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "18", "text": "老板说要有语录，于是就有了语录", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "19", "text": "我太难了，但我会努力的！", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        {"id": "20", "text": "这个bug不是我的锅，是...是天气的锅！", "category": "funny", "created_at": "2024-01-01T00:00:00"},
        
        # 抽象语录
        {"id": "21", "text": "人生就像房产分析，充满了未知与可能", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "22", "text": "每一次点击，都是一次心灵的对话", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "23", "text": "数据不说话，但它在思考", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "24", "text": "我们终将在数据的海洋中相遇", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "25", "text": "今天的你，也在为梦想努力吗？", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "26", "text": "房产有价，梦想无价", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "27", "text": "每一栋房子，都承载着一个故事", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "28", "text": "在代码的世界里，我们都是追梦人", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "29", "text": "有时候，慢下来也是一种前进", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        {"id": "30", "text": "你看到的不是数据，是生活的缩影", "category": "abstract", "created_at": "2024-01-01T00:00:00"},
        
        # 鼓励语录
        {"id": "31", "text": "加油！你离目标又近了一步！", "category": "encourage", "created_at": "2024-01-01T00:00:00"},
        {"id": "32", "text": "不要放弃，成功就在下一个转角", "category": "encourage", "created_at": "2024-01-01T00:00:00"},
        {"id": "33", "text": "相信自己，你比想象中更强大", "category": "encourage", "created_at": "2024-01-01T00:00:00"},
        {"id": "34", "text": "每一次尝试，都是成长的机会", "category": "encourage", "created_at": "2024-01-01T00:00:00"},
        {"id": "35", "text": "累了就休息一下，但不要放弃", "category": "encourage", "created_at": "2024-01-01T00:00:00"},
        
        # 房产专业语录
        {"id": "36", "text": "地段、地段、还是地段！", "category": "professional", "created_at": "2024-01-01T00:00:00"},
        {"id": "37", "text": "买房三要素：位置、价格、品质", "category": "professional", "created_at": "2024-01-01T00:00:00"},
        {"id": "38", "text": "投资房产，要看长远价值", "category": "professional", "created_at": "2024-01-01T00:00:00"},
        {"id": "39", "text": "好房子不等人，决策要果断", "category": "professional", "created_at": "2024-01-01T00:00:00"},
        {"id": "40", "text": "数据分析让投资更理性", "category": "professional", "created_at": "2024-01-01T00:00:00"},
    ]
    
    if category:
        quotes = [q for q in quotes if q["category"] == category]
    
    return {"quotes": quotes, "total": len(quotes), "limit": limit, "offset": offset}


@router.post("/quotes")
async def create_quote(
    quote: MascotQuoteCreate,
    current_user: dict = Depends(require_admin)
):
    """创建新语录"""
    new_quote = {
        "id": str(uuid.uuid4()),
        "text": quote.text,
        "category": quote.category,
        "created_at": datetime.utcnow().isoformat(),
    }
    logger.info(f"Admin {current_user['id']} created mascot quote: {quote.text[:30]}...")
    return {"success": True, "quote": new_quote}


@router.put("/quotes/{quote_id}")
async def update_quote(
    quote_id: str,
    quote: MascotQuoteUpdate,
    current_user: dict = Depends(require_admin)
):
    """更新语录"""
    logger.info(f"Admin {current_user['id']} updated mascot quote {quote_id}")
    return {"success": True, "message": "语录更新成功"}


@router.delete("/quotes/{quote_id}")
async def delete_quote(
    quote_id: str,
    current_user: dict = Depends(require_admin)
):
    """删除语录"""
    logger.info(f"Admin {current_user['id']} deleted mascot quote {quote_id}")
    return {"success": True, "message": "语录删除成功"}


@router.get("/stats", response_model=MascotStats)
async def get_stats(
    current_user: dict = Depends(require_admin)
):
    """获取吉祥物互动统计"""
    return MascotStats(
        total_clicks=1234,
        total_drag_events=567,
        total_scene_triggers=890,
        clicks_today=45,
        popular_scenes=[
            {"scene": "task_loading", "count": 234},
            {"scene": "task_complete", "count": 189},
            {"scene": "welcome", "count": 156},
        ],
        recent_interactions=[
            {"type": "click", "user_id": "xxx", "time": "2024-01-01T12:00:00"},
            {"type": "drag", "user_id": "yyy", "time": "2024-01-01T11:30:00"},
        ]
    )


@router.post("/interaction")
async def report_interaction(
    event_type: str,
    scene: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """用户端上报互动事件"""
    logger.info(f"Mascot interaction: {event_type} by user {current_user['id']}")
    return {"success": True}
