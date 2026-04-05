"""
增强功能模块 - 综合API路由
包含通知、公告、反馈、活动、兑换码、用户等级、勋章、排行榜等
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import json
import uuid
import random
import string

from backend.auth import get_current_user
from backend.database_pg import get_db

router = APIRouter(prefix="/api/enhanced", tags=["增强功能模块"])


# ==================== 通知系统 ====================

class NotificationCreate(BaseModel):
    user_id: str
    type: str
    title: str
    content: str
    data: Dict[str, Any] = None
    channel: str = "in_app"

@router.post("/notifications")
async def create_notification(
    notification: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    async with get_db() as db:
        notification_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO notifications (id, user_id, type, title, content, data, channel, sent_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, notification_id, notification.user_id, notification.type,
            notification.title, notification.content,
            json.dumps(notification.data or {}, ensure_ascii=False),
            notification.channel, datetime.utcnow())
        
        return {"success": True, "id": notification_id}

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        if unread_only:
            rows = await db.fetch("""
                SELECT * FROM notifications 
                WHERE user_id = $1 AND is_read = FALSE
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)
        else:
            rows = await db.fetch("""
                SELECT * FROM notifications 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)
        
        unread_count = await db.fetchone("""
            SELECT COUNT(*) FROM notifications 
            WHERE user_id = $1 AND is_read = FALSE
        """, user_id)
        
        notifications = []
        for row in rows:
            notifications.append({
                "id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "data": json.loads(row["data"]) if row["data"] else {},
                "is_read": row["is_read"],
                "created_at": str(row["created_at"]),
            })
        
        return {
            "notifications": notifications,
            "unread_count": unread_count[0] if unread_count else 0
        }

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        await db.execute("""
            UPDATE notifications 
            SET is_read = TRUE, read_at = $1
            WHERE id = $2 AND user_id = $3
        """, datetime.utcnow(), notification_id, user_id)
        
        return {"success": True}

@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        await db.execute("""
            UPDATE notifications 
            SET is_read = TRUE, read_at = $1
            WHERE user_id = $2 AND is_read = FALSE
        """, datetime.utcnow(), user_id)
        
        return {"success": True}


# ==================== 公告系统 ====================

@router.get("/announcements")
async def list_announcements(
    category: str = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    async with get_db() as db:
        conditions = ["is_active = TRUE", 
                      "(start_time IS NULL OR start_time <= CURRENT_TIMESTAMP)",
                      "(end_time IS NULL OR end_time >= CURRENT_TIMESTAMP)"]
        params = []
        
        if category:
            conditions.append(f"category = ${len(params) + 1}")
            params.append(category)
        
        where_clause = " AND ".join(conditions)
        params.append(limit)
        
        rows = await db.fetch(f"""
            SELECT * FROM announcements 
            WHERE {where_clause}
            ORDER BY priority DESC, created_at DESC
            LIMIT ${len(params)}
        """, *params)
        
        announcements = []
        for row in rows:
            announcements.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "category": row["category"],
                "is_popup": row["is_popup"],
                "created_at": str(row["created_at"]),
            })
        
        return {"announcements": announcements}

@router.post("/announcements/{announcement_id}/view")
async def increment_announcement_view(
    announcement_id: str
):
    async with get_db() as db:
        await db.execute("""
            UPDATE announcements SET view_count = view_count + 1
            WHERE id = $1
        """, announcement_id)
        
        return {"success": True}


# ==================== 反馈系统 ====================

class FeedbackCreate(BaseModel):
    type: str = Field(default="feedback", description="feedback/suggestion/complaint")
    subject: str
    content: str
    rating: int = Field(default=None, ge=1, le=5)

@router.post("/feedbacks")
async def create_feedback(
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        feedback_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO user_feedbacks (id, user_id, type, subject, content, rating)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, feedback_id, user_id, feedback.type, feedback.subject,
            feedback.content, feedback.rating)
        
        return {"success": True, "id": feedback_id}

@router.get("/feedbacks")
async def list_user_feedbacks(
    status: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        if status:
            rows = await db.fetch("""
                SELECT * FROM user_feedbacks 
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC
            """, user_id, status)
        else:
            rows = await db.fetch("""
                SELECT * FROM user_feedbacks 
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, user_id)
        
        feedbacks = []
        for row in rows:
            feedbacks.append({
                "id": row["id"],
                "type": row["type"],
                "subject": row["subject"],
                "status": row["status"],
                "reply": row["reply"],
                "rating": row["rating"],
                "created_at": str(row["created_at"]),
            })
        
        return {"feedbacks": feedbacks}


# ==================== 活动系统 ====================

@router.get("/activities")
async def list_activities(
    activity_type: str = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    async with get_db() as db:
        conditions = ["is_active = TRUE",
                      "start_time <= CURRENT_TIMESTAMP",
                      "end_time >= CURRENT_TIMESTAMP"]
        params = []
        
        if activity_type:
            conditions.append(f"type = ${len(params) + 1}")
            params.append(activity_type)
        
        where_clause = " AND ".join(conditions)
        params.append(limit)
        
        rows = await db.fetch(f"""
            SELECT * FROM activities 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
        """, *params)
        
        activities = []
        for row in rows:
            activities.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "type": row["type"],
                "rules": json.loads(row["rules"]) if row["rules"] else {},
                "rewards": json.loads(row["rewards"]) if row["rewards"] else {},
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "banner_url": row["banner_url"],
                "current_participants": row["current_participants"],
            })
        
        return {"activities": activities}

@router.post("/activities/{activity_id}/join")
async def join_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        activity = await db.fetchone(
            "SELECT * FROM activities WHERE id = $1", activity_id
        )
        
        if not activity:
            raise HTTPException(status_code=404, detail="活动不存在")
        
        existing = await db.fetchone("""
            SELECT id FROM activity_participations 
            WHERE activity_id = $1 AND user_id = $2
        """, activity_id, user_id)
        
        if existing:
            raise HTTPException(status_code=400, detail="已参与该活动")
        
        participation_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO activity_participations (id, activity_id, user_id)
            VALUES ($1, $2, $3)
        """, participation_id, activity_id, user_id)
        
        await db.execute("""
            UPDATE activities SET current_participants = current_participants + 1
            WHERE id = $1
        """, activity_id)
        
        return {"success": True, "participation_id": participation_id}

@router.get("/activities/{activity_id}/progress")
async def get_activity_progress(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        participation = await db.fetchone("""
            SELECT * FROM activity_participations 
            WHERE activity_id = $1 AND user_id = $2
        """, activity_id, user_id)
        
        if not participation:
            return {"participated": False}
        
        return {
            "participated": True,
            "progress": json.loads(participation["progress"]) if participation["progress"] else {},
            "is_completed": participation["is_completed"],
            "reward_claimed": participation["reward_claimed"],
        }


# ==================== 兑换码系统 ====================

class RedemptionRequest(BaseModel):
    code: str

@router.post("/redeem")
async def redeem_code(
    request: RedemptionRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        code_info = await db.fetchone(
            "SELECT * FROM redemption_codes WHERE code = $1", request.code
        )
        
        if not code_info:
            raise HTTPException(status_code=404, detail="兑换码无效")
        
        if not code_info["is_active"]:
            raise HTTPException(status_code=400, detail="兑换码已失效")
        
        if code_info["end_time"] and datetime.utcnow() > code_info["end_time"]:
            raise HTTPException(status_code=400, detail="兑换码已过期")
        
        if code_info["used_count"] >= code_info["max_uses"]:
            raise HTTPException(status_code=400, detail="兑换码已用完")
        
        existing = await db.fetchone("""
            SELECT id FROM redemption_logs 
            WHERE code_id = $1 AND user_id = $2
        """, code_info["id"], user_id)
        
        if existing:
            raise HTTPException(status_code=400, detail="您已使用过此兑换码")
        
        reward_type = code_info["type"]
        reward_value = code_info["value"]
        
        if reward_type == "integral":
            amount = int(reward_value)
            await db.execute("""
                UPDATE users SET integral = integral + $1 WHERE id = $2
            """, amount, user_id)
            
            balance_row = await db.fetchone("SELECT integral FROM users WHERE id = $1", user_id)
            balance = balance_row[0] if balance_row else 0
            
            await db.execute("""
                INSERT INTO integral_logs (id, user_id, type, amount, balance, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, str(uuid.uuid4()), user_id, "redemption", amount, balance, f"兑换码兑换: {code_info['description']}")
        
        await db.execute("""
            UPDATE redemption_codes SET used_count = used_count + 1
            WHERE id = $1
        """, code_info["id"])
        
        log_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO redemption_logs (id, code_id, user_id, reward_type, reward_value)
            VALUES ($1, $2, $3, $4, $5)
        """, log_id, code_info["id"], user_id, reward_type, reward_value)
        
        return {
            "success": True,
            "reward_type": reward_type,
            "reward_value": reward_value,
            "message": f"兑换成功！获得{reward_value}{'积分' if reward_type == 'integral' else ''}"
        }


# ==================== 用户等级系统 ====================

@router.get("/user/level")
async def get_user_level(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        level_info = await db.fetchone("""
            SELECT * FROM user_levels WHERE user_id = $1
        """, user_id)
        
        if not level_info:
            level_info = await db.fetchone("""
                INSERT INTO user_levels (id, user_id)
                VALUES ($1, $2)
                RETURNING *
            """, str(uuid.uuid4()), user_id)
        
        level_config = await db.fetchone("""
            SELECT * FROM level_configs WHERE level = $1
        """, level_info["level"])
        
        next_level_config = await db.fetchone("""
            SELECT * FROM level_configs WHERE level = $1
        """, level_info["level"] + 1)
        
        return {
            "level": level_info["level"],
            "exp": level_info["exp"],
            "total_exp": level_info["total_exp"],
            "level_name": level_config["name"] if level_config else "未知",
            "level_icon": level_config["icon"] if level_config else "🌱",
            "next_level_exp": next_level_config["min_exp"] if next_level_config else None,
            "daily_checkin_streak": level_info["daily_checkin_streak"],
            "max_checkin_streak": level_info["max_checkin_streak"],
            "tasks_completed": level_info["tasks_completed"],
            "invitations_count": level_info["invitations_count"],
        }

@router.post("/user/exp/add")
async def add_user_exp(
    amount: int = Query(..., ge=1),
    reason: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        level_info = await db.fetchone(
            "SELECT * FROM user_levels WHERE user_id = $1", user_id
        )
        
        if not level_info:
            await db.execute("""
                INSERT INTO user_levels (id, user_id, exp, total_exp)
                VALUES ($1, $2, $3, $3)
            """, str(uuid.uuid4()), user_id, amount)
        else:
            new_exp = level_info["exp"] + amount
            new_total = level_info["total_exp"] + amount
            current_level = level_info["level"]
            
            next_level = await db.fetchone(
                "SELECT * FROM level_configs WHERE level = $1", current_level + 1
            )
            
            if next_level and new_exp >= next_level["min_exp"]:
                current_level += 1
                new_exp = new_exp - next_level["min_exp"]
            
            await db.execute("""
                UPDATE user_levels 
                SET exp = $1, total_exp = $2, level = $3, updated_at = $4
                WHERE user_id = $5
            """, new_exp, new_total, current_level, datetime.utcnow(), user_id)
        
        return {"success": True, "exp_added": amount}


# ==================== 勋章系统 ====================

@router.get("/badges")
async def list_all_badges():
    async with get_db() as db:
        rows = await db.fetch("""
            SELECT * FROM badges WHERE is_active = TRUE
            ORDER BY category, created_at
        """)
        
        badges = []
        for row in rows:
            badges.append({
                "id": row["id"],
                "code": row["code"],
                "name": row["name"],
                "description": row["description"],
                "icon": row["icon"],
                "category": row["category"],
            })
        
        return {"badges": badges}

@router.get("/user/badges")
async def get_user_badges(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    async with get_db() as db:
        rows = await db.fetch("""
            SELECT ub.*, b.code, b.name, b.description, b.icon, b.category
            FROM user_badges ub
            JOIN badges b ON ub.badge_id = b.id
            WHERE ub.user_id = $1
            ORDER BY ub.earned_at DESC
        """, user_id)
        
        badges = []
        for row in rows:
            badges.append({
                "id": row["id"],
                "badge_id": row["badge_id"],
                "code": row["code"],
                "name": row["name"],
                "description": row["description"],
                "icon": row["icon"],
                "category": row["category"],
                "earned_at": str(row["earned_at"]),
                "is_displayed": row["is_displayed"],
            })
        
        return {"badges": badges}

@router.post("/user/badges/check")
async def check_and_award_badges(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    awarded = []
    
    async with get_db() as db:
        all_badges = await db.fetch(
            "SELECT * FROM badges WHERE is_active = TRUE"
        )
        
        earned_badge_ids = await db.fetch("""
            SELECT badge_id FROM user_badges WHERE user_id = $1
        """, user_id)
        earned_ids = {row[0] for row in earned_badge_ids}
        
        for badge in all_badges:
            if badge["id"] in earned_ids:
                continue
            
            cond_type = badge["condition_type"]
            cond_value = badge["condition_value"]
            
            should_award = False
            
            if cond_type == "checkin_count":
                count = await db.fetchone("""
                    SELECT COUNT(*) FROM checkin_logs WHERE user_id = $1
                """, user_id)
                if count and count[0] >= int(cond_value):
                    should_award = True
            
            elif cond_type == "checkin_streak":
                level_info = await db.fetchone(
                    "SELECT max_checkin_streak FROM user_levels WHERE user_id = $1", user_id
                )
                if level_info and level_info[0] >= int(cond_value):
                    should_award = True
            
            elif cond_type == "agent_count":
                count = await db.fetchone("""
                    SELECT COUNT(*) FROM user_agents WHERE user_id = $1
                """, user_id)
                if count and count[0] >= int(cond_value):
                    should_award = True
            
            elif cond_type == "task_count":
                count = await db.fetchone("""
                    SELECT COUNT(*) FROM analysis_tasks WHERE user_id = $1 AND status = 'completed'
                """, user_id)
                if count and count[0] >= int(cond_value):
                    should_award = True
            
            if should_award:
                await db.execute("""
                    INSERT INTO user_badges (id, user_id, badge_id)
                    VALUES ($1, $2, $3)
                """, str(uuid.uuid4()), user_id, badge["id"])
                awarded.append({
                    "name": badge["name"],
                    "icon": badge["icon"],
                })
    
    return {"awarded_badges": awarded}


# ==================== 排行榜系统 ====================

@router.get("/leaderboard")
async def get_leaderboard(
    type: str = Query("integral", description="integral/tasks/invitations"),
    period: str = Query("weekly", description="daily/weekly/monthly/all"),
    limit: int = Query(20, ge=1, le=100)
):
    today = date.today()
    
    if period == "daily":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start_date = today.replace(day=1)
    else:
        start_date = date(2020, 1, 1)
    
    async with get_db() as db:
        if type == "integral":
            if period == "all":
                rows = await db.fetch("""
                    SELECT u.id, u.email, u.username, u.integral as score
                    FROM users u
                    WHERE u.integral > 0
                    ORDER BY u.integral DESC
                    LIMIT $1
                """, limit)
            else:
                rows = await db.fetch("""
                    SELECT u.id, u.email, u.username, COALESCE(SUM(il.amount), 0) as score
                    FROM users u
                    LEFT JOIN integral_logs il ON u.id = il.user_id
                        AND il.created_at >= $1
                    GROUP BY u.id, u.email, u.username
                    HAVING COALESCE(SUM(il.amount), 0) > 0
                    ORDER BY score DESC
                    LIMIT $2
                """, datetime.combine(start_date, datetime.min.time()), limit)
        
        elif type == "tasks":
            rows = await db.fetch("""
                SELECT u.id, u.email, u.username, COUNT(t.id) as score
                FROM users u
                LEFT JOIN analysis_tasks t ON u.id = t.user_id
                    AND t.status = 'completed'
                    AND t.completed_at >= $1
                GROUP BY u.id, u.email, u.username
                HAVING COUNT(t.id) > 0
                ORDER BY score DESC
                LIMIT $2
            """, datetime.combine(start_date, datetime.min.time()), limit)
        
        elif type == "invitations":
            rows = await db.fetch("""
                SELECT u.id, u.email, u.username, ul.invitations_count as score
                FROM users u
                LEFT JOIN user_levels ul ON u.id = ul.user_id
                WHERE ul.invitations_count > 0
                ORDER BY ul.invitations_count DESC
                LIMIT $1
            """, limit)
        
        else:
            rows = []
        
        leaderboard = []
        for i, row in enumerate(rows, 1):
            leaderboard.append({
                "rank": i,
                "user_id": row[0],
                "username": row[2] or row[1].split('@')[0],
                "score": row[3],
            })
        
        return {
            "type": type,
            "period": period,
            "leaderboard": leaderboard,
            "updated_at": datetime.utcnow().isoformat(),
        }


# ==================== 帮助中心 ====================

@router.get("/help/articles")
async def list_help_articles(
    category: str = Query(None),
    search: str = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    async with get_db() as db:
        conditions = ["is_published = TRUE"]
        params = []
        
        if category:
            conditions.append(f"category = ${len(params) + 1}")
            params.append(category)
        
        if search:
            conditions.append(f"(title ILIKE ${len(params) + 1} OR content ILIKE ${len(params) + 1})")
            params.append(f"%{search}%")
        
        where_clause = " AND ".join(conditions)
        params.append(limit)
        
        rows = await db.fetch(f"""
            SELECT id, title, category, tags, view_count, created_at
            FROM help_articles 
            WHERE {where_clause}
            ORDER BY sort_order, view_count DESC
            LIMIT ${len(params)}
        """, *params)
        
        articles = []
        for row in rows:
            articles.append({
                "id": row[0],
                "title": row[1],
                "category": row[2],
                "tags": json.loads(row[3]) if row[3] else [],
                "view_count": row[4],
            })
        
        return {"articles": articles}

@router.get("/help/articles/{article_id}")
async def get_help_article(article_id: str):
    async with get_db() as db:
        article = await db.fetchone("""
            SELECT * FROM help_articles WHERE id = $1 AND is_published = TRUE
        """, article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        await db.execute("""
            UPDATE help_articles SET view_count = view_count + 1 WHERE id = $1
        """, article_id)
        
        return {
            "id": article["id"],
            "title": article["title"],
            "content": article["content"],
            "category": article["category"],
            "tags": json.loads(article["tags"]) if article["tags"] else [],
            "view_count": article["view_count"] + 1,
        }
