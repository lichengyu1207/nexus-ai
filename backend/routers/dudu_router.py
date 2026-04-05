"""
嘟嘟吉祥物API路由
Dudu Mascot API Router

提供吉祥物状态、互动、装扮等REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import random

from ..agents.dudu_agent import (
    dudu_manager, DuduAgent, DuduManager,
    EmotionType, ActionType, EventType,
    EmotionEngine, DuduQuoteEngine
)


router = APIRouter(prefix="/api/dudu", tags=["dudu"])


class ClickRequest(BaseModel):
    user_id: str


class FeedRequest(BaseModel):
    user_id: str
    food_type: str = "default"
    integral_cost: int = 10


class EventRequest(BaseModel):
    user_id: str
    event_type: str
    data: Optional[Dict[str, Any]] = None


class EquipCostumeRequest(BaseModel):
    user_id: str
    costume_id: str


class BuyCostumeRequest(BaseModel):
    user_id: str
    costume_id: str


def get_user_id() -> str:
    """获取当前用户ID（简化版，实际应从JWT获取）"""
    return "default_user"


@router.get("/state/{user_id}")
async def get_dudu_state(user_id: str):
    """获取嘟嘟状态"""
    try:
        dudu = await dudu_manager.get_dudu(user_id)
        return dudu.get_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/click")
async def click_dudu(request: ClickRequest):
    """点击嘟嘟"""
    try:
        state = await dudu_manager.broadcast_event(
            request.user_id,
            EventType.USER_CLICK
        )
        
        integral_bonus = random.randint(1, 5)
        
        return {
            "success": True,
            "state": state,
            "integral_bonus": integral_bonus,
            "message": state.get("current_message", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feed")
async def feed_dudu(request: FeedRequest):
    """喂食嘟嘟"""
    try:
        food_values = {
            "default": 10,
            "deluxe": 25,
            "premium": 50
        }
        
        food_value = food_values.get(request.food_type, 10)
        
        state = await dudu_manager.broadcast_event(
            request.user_id,
            EventType.USER_FEED,
            {"value": food_value, "integral_cost": request.integral_cost}
        )
        
        return {
            "success": True,
            "state": state,
            "intimacy_gain": food_value // 2,
            "message": state.get("current_message", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event")
async def trigger_event(request: EventRequest):
    """触发事件"""
    try:
        event_type_map = {
            "user_login": EventType.USER_LOGIN,
            "user_logout": EventType.USER_LOGOUT,
            "task_complete": EventType.TASK_COMPLETE,
            "task_fail": EventType.TASK_FAIL,
            "integral_gained": EventType.INTEGRAL_GAINED,
            "integral_spent": EventType.INTEGRAL_SPENT,
            "risk_alert": EventType.RISK_ALERT,
            "new_feature": EventType.NEW_FEATURE,
            "achievement_unlock": EventType.ACHIEVEMENT_UNLOCK,
            "sign_in": EventType.SIGN_IN,
            "invite_success": EventType.INVITE_SUCCESS,
            "report_generated": EventType.REPORT_GENERATED,
        }
        
        event_type = event_type_map.get(request.event_type)
        if not event_type:
            raise HTTPException(status_code=400, detail=f"未知事件类型: {request.event_type}")
        
        state = await dudu_manager.broadcast_event(
            request.user_id,
            event_type,
            request.data
        )
        
        return {
            "success": True,
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costumes/{user_id}")
async def get_costumes(user_id: str):
    """获取装扮列表"""
    try:
        from ..database import get_db_connection
        
        dudu = await dudu_manager.get_dudu(user_id)
        user_level = dudu.level_info.level
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT costume_id, name, description, category, rarity, price, unlock_level, preview_url
                    FROM dudu_costume_shop
                    WHERE is_active = TRUE
                    ORDER BY rarity DESC, price ASC
                """)
                
                owned_rows = await conn.fetch("""
                    SELECT costume_id, equipped
                    FROM dudu_user_costumes
                    WHERE user_id = $1
                """, user_id)
                
                owned_costumes = {row["costume_id"]: row["equipped"] for row in owned_rows}
                
                costumes = []
                for row in rows:
                    costume = dict(row)
                    costume["owned"] = row["costume_id"] in owned_costumes
                    costume["equipped"] = owned_costumes.get(row["costume_id"], False)
                    costume["unlocked"] = user_level >= row["unlock_level"]
                    costumes.append(costume)
                
                return {
                    "costumes": costumes,
                    "user_level": user_level
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/equip-costume")
async def equip_costume(request: EquipCostumeRequest):
    """装备装扮"""
    try:
        dudu = await dudu_manager.get_dudu(request.user_id)
        
        success = dudu.equip_costume(request.costume_id)
        
        if success:
            from ..database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        UPDATE dudu_user_costumes
                        SET equipped = FALSE
                        WHERE user_id = $1
                    """, request.user_id)
                    
                    await conn.execute("""
                        UPDATE dudu_user_costumes
                        SET equipped = TRUE
                        WHERE user_id = $1 AND costume_id = $2
                    """, request.user_id, request.costume_id)
                    
                    await conn.commit()
                finally:
                    await conn.close()
            
            await dudu._save_state()
        
        return {
            "success": success,
            "state": dudu.get_state()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buy-costume")
async def buy_costume(request: BuyCostumeRequest):
    """购买装扮"""
    try:
        from ..database import get_db_connection
        
        dudu = await dudu_manager.get_dudu(request.user_id)
        
        async for conn in get_db_connection():
            try:
                costume = await conn.fetchrow("""
                    SELECT costume_id, name, price, unlock_level
                    FROM dudu_costume_shop
                    WHERE costume_id = $1 AND is_active = TRUE
                """, request.costume_id)
                
                if not costume:
                    return {"success": False, "message": "装扮不存在"}
                
                if dudu.level_info.level < costume["unlock_level"]:
                    return {"success": False, "message": f"等级不足，需要{costume['unlock_level']}级"}
                
                owned = await conn.fetchrow("""
                    SELECT id FROM dudu_user_costumes
                    WHERE user_id = $1 AND costume_id = $2
                """, request.user_id, request.costume_id)
                
                if owned:
                    return {"success": False, "message": "已拥有此装扮"}
                
                return {
                    "success": True,
                    "costume": dict(costume),
                    "message": f"确认购买 {costume['name']}？需要 {costume['price']} 积分"
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-buy-costume")
async def confirm_buy_costume(request: BuyCostumeRequest):
    """确认购买装扮"""
    try:
        from ..database import get_db_connection
        
        dudu = await dudu_manager.get_dudu(request.user_id)
        
        async for conn in get_db_connection():
            try:
                costume = await conn.fetchrow("""
                    SELECT costume_id, name, price, unlock_level
                    FROM dudu_costume_shop
                    WHERE costume_id = $1 AND is_active = TRUE
                """, request.costume_id)
                
                if not costume:
                    return {"success": False, "message": "装扮不存在"}
                
                await conn.execute("""
                    INSERT INTO dudu_user_costumes (user_id, costume_id, purchased_at)
                    VALUES ($1, $2, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, costume_id) DO NOTHING
                """, request.user_id, request.costume_id)
                
                await conn.commit()
                
                return {
                    "success": True,
                    "message": f"成功购买 {costume['name']}！",
                    "integral_spent": costume["price"]
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/{category}")
async def get_quotes(category: str, limit: int = Query(5, ge=1, le=20)):
    """获取语录"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT content, priority
                    FROM dudu_quotes
                    WHERE category = $1 AND is_active = TRUE
                    ORDER BY priority DESC, RANDOM()
                    LIMIT $2
                """, category, limit)
                
                quotes = [row["content"] for row in rows]
                
                if not quotes:
                    quote = DuduQuoteEngine.get_quote(category)
                    quotes = [quote]
                
                return {
                    "category": category,
                    "quotes": quotes
                }
            finally:
                await conn.close()
    except Exception as e:
        quote = DuduQuoteEngine.get_quote(category)
        return {"category": category, "quotes": [quote]}


@router.get("/random-action/{user_id}")
async def get_random_action(user_id: str):
    """获取随机动作"""
    try:
        dudu = await dudu_manager.get_dudu(user_id)
        emotion, action, message = dudu.get_random_action()
        
        return {
            "emotion": emotion.value,
            "action": action.value,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interactions/{user_id}")
async def get_interaction_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=30)
):
    """获取互动历史"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT interaction_type, event_data, intimacy_change, exp_change, integral_change, created_at
                    FROM dudu_interactions
                    WHERE user_id = $1 AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                    ORDER BY created_at DESC
                    LIMIT $2
                """ % days, user_id, limit)
                
                interactions = [dict(row) for row in rows]
                
                return {
                    "user_id": user_id,
                    "interactions": interactions,
                    "total": len(interactions)
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements/{user_id}")
async def get_achievements(user_id: str):
    """获取成就列表"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT achievement_id, unlocked_at
                    FROM dudu_achievements
                    WHERE user_id = $1
                    ORDER BY unlocked_at DESC
                """, user_id)
                
                achievements = [dict(row) for row in rows]
                
                all_achievements = [
                    {"id": "first_click", "name": "初次相遇", "description": "第一次点击嘟嘟"},
                    {"id": "feed_master", "name": "投喂达人", "description": "累计喂食100次"},
                    {"id": "level_10", "name": "成长之路", "description": "嘟嘟达到10级"},
                    {"id": "level_20", "name": "形影不离", "description": "嘟嘟达到20级"},
                    {"id": "costume_collector", "name": "装扮收藏家", "description": "拥有10件装扮"},
                    {"id": "daily_visitor", "name": "每日访客", "description": "连续登录7天"},
                    {"id": "intimacy_50", "name": "亲密伙伴", "description": "亲密度达到50"},
                    {"id": "intimacy_100", "name": "灵魂伴侣", "description": "亲密度达到100"},
                ]
                
                unlocked_ids = {a["achievement_id"] for a in achievements}
                
                for ach in all_achievements:
                    ach["unlocked"] = ach["id"] in unlocked_ids
                
                return {
                    "user_id": user_id,
                    "achievements": all_achievements,
                    "unlocked_count": len(achievements)
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{user_id}")
async def get_dudu_stats(user_id: str):
    """获取嘟嘟统计信息"""
    try:
        from ..database import get_db_connection
        
        dudu = await dudu_manager.get_dudu(user_id)
        
        async for conn in get_db_connection():
            try:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        COUNT(CASE WHEN interaction_type = 'feed' THEN 1 END) as feed_count,
                        COUNT(CASE WHEN interaction_type = 'click' THEN 1 END) as click_count,
                        SUM(intimacy_change) as total_intimacy_gain,
                        SUM(exp_change) as total_exp_gain
                    FROM dudu_interactions
                    WHERE user_id = $1
                """, user_id)
                
                costume_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM dudu_user_costumes WHERE user_id = $1
                """, user_id)
                
                return {
                    "user_id": user_id,
                    "level": dudu.level_info.level,
                    "total_interactions": stats["total_interactions"] or 0,
                    "feed_count": stats["feed_count"] or 0,
                    "click_count": stats["click_count"] or 0,
                    "total_intimacy_gain": stats["total_intimacy_gain"] or 0,
                    "total_exp_gain": stats["total_exp_gain"] or 0,
                    "costume_count": costume_count or 0,
                    "emotion_state": dudu.emotion_state.to_dict()
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{user_id}")
async def dudu_websocket(websocket, user_id: str):
    """WebSocket连接，实时推送嘟嘟状态"""
    await websocket.accept()
    
    try:
        dudu = await dudu_manager.get_dudu(user_id)
        
        await websocket.send_json({
            "type": "init",
            "state": dudu.get_state()
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "click":
                state = await dudu_manager.broadcast_event(user_id, EventType.USER_CLICK)
                await websocket.send_json({
                    "type": "state_update",
                    "state": state
                })
            elif data.get("type") == "feed":
                state = await dudu_manager.broadcast_event(
                    user_id, 
                    EventType.USER_FEED,
                    data.get("data", {})
                )
                await websocket.send_json({
                    "type": "state_update",
                    "state": state
                })
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
