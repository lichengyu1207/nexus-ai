"""
用户习惯培养系统API路由 - PostgreSQL版本
包含签到、任务、等级等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
import uuid
import logging

from backend.database_pg import get_db
from backend.routers.auth import get_current_user
from backend.services.integral import IntegralService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/habit", tags=["habit"])


class SigninStatusResponse(BaseModel):
    today_signed: bool
    consecutive_days: int
    total_signin_days: int
    repent_cards: int
    month_records: List[str]
    today_reward: int


class SigninResponse(BaseModel):
    success: bool
    reward_integral: int
    reward_tokens: int
    consecutive_days: int
    message: str


class RepentRequest(BaseModel):
    date: str


class BuyRepentRequest(BaseModel):
    quantity: int = 1


class TaskProgressResponse(BaseModel):
    task_id: str
    name: str
    description: Optional[str]
    type: str
    target_action: str
    target_count: int
    current_progress: int
    reward_integral: int
    status: str


class LevelInfoResponse(BaseModel):
    level: int
    total_points: int
    next_level_points: int
    current_level_points: int
    benefits: Optional[dict]


@router.get("/signin/status", response_model=SigninStatusResponse)
async def get_signin_status(user = Depends(get_current_user)):
    async with get_db() as conn:
        today = date.today().isoformat()
        
        today_signed = await conn.fetchval(
            "SELECT COUNT(*) FROM signin_records WHERE user_id = $1 AND signin_date = $2",
            user["id"], today
        )
        
        consecutive_row = await conn.fetchrow(
            """
            SELECT consecutive_days, total_signin_days 
            FROM users WHERE id = $1
            """,
            user["id"]
        )
        
        repent_cards = await conn.fetchval(
            "SELECT COUNT(*) FROM repent_records WHERE user_id = $1",
            user["id"]
        )
        
        month_records = await conn.fetch(
            """
            SELECT signin_date::text 
            FROM signin_records 
            WHERE user_id = $1 
            AND signin_date >= $1 
            ORDER BY signin_date DESC
            """,
            user["id"],
            (datetime.now() - timedelta(days=30)).isoformat()
        )
        
        today_reward = 10
        if consecutive_row and consecutive_row["consecutive_days"] >= 7:
            today_reward = 20
        
        return SigninStatusResponse(
            today_signed=today_signed > 0,
            consecutive_days=consecutive_row["consecutive_days"] if consecutive_row else 0,
            total_signin_days=consecutive_row["total_signin_days"] if consecutive_row else 0,
            repent_cards=repent_cards or 0,
            month_records=[r["signin_date"] for r in month_records],
            today_reward=today_reward
        )


@router.post("/signin", response_model=SigninResponse)
async def do_signin(user = Depends(get_current_user)):
    async with get_db() as conn:
        today = date.today().isoformat()
        
        existing = await conn.fetchval(
            "SELECT COUNT(*) FROM signin_records WHERE user_id = $1 AND signin_date = $2",
            user["id"], today
        )
        
        if existing > 0:
            raise HTTPException(status_code=400, detail="今日已签到")
        
        consecutive_days = 1
        row = await conn.fetchrow(
            "SELECT consecutive_days, last_signin_date FROM users WHERE id = $1",
            user["id"]
        )
        
        if row and row["last_signin_date"]:
            last_signin = row["last_signin_date"]
            if isinstance(last_signin, str):
                last_signin_date = datetime.fromisoformat(last_signin).date()
            else:
                last_signin_date = last_signin.date()
            
            if (date.today() - last_signin_date).days == 1:
                consecutive_days = row["consecutive_days"] + 1
        
        await conn.execute(
            """
            UPDATE users 
            SET consecutive_days = $1,
                total_signin_days = total_signin_days + 1,
                last_signin_date = $2
            WHERE id = $3
            """,
            consecutive_days,
            user["total_signin_days"] + 1 if user.get("total_signin_days") else 1,
            today,
            user["id"]
        )
        
        reward_integral = 10
        if consecutive_days >= 7:
            reward_integral = 20
        
        await conn.execute(
            """
            INSERT INTO signin_records (id, user_id, signin_date, reward_integral)
            VALUES ($1, $2, $3, $4)
            """,
            str(uuid.uuid4()), user["id"], today, reward_integral
        )
        
        integral_service = IntegralService()
        await integral_service.add_integral(user["id"], reward_integral, "签到奖励")
        
        return SigninResponse(
            success=True,
            reward_integral=reward_integral,
            reward_tokens=0,
            consecutive_days=consecutive_days,
            message=f"签到成功！连续签到{consecutive_days}天"
        )


@router.post("/repent", response_model=SigninResponse)
async def use_repent(request: RepentRequest, user = Depends(get_current_user)):
    async with get_db() as conn:
        repent_date = datetime.fromisoformat(request.date).date()
        
        existing = await conn.fetchval(
            "SELECT COUNT(*) FROM repent_records WHERE user_id = $1 AND repent_date = $2",
            user["id"], repent_date.isoformat()
        )
        
        if existing > 0:
            raise HTTPException(status_code=400, detail="该日期已补签")
        
        await conn.execute(
            """
            INSERT INTO repent_records (id, user_id, repent_date, created_at)
            VALUES ($1, $2, $3, NOW())
            """,
            str(uuid.uuid4()), user["id"], repent_date.isoformat()
        )
        
        await conn.execute(
            """
            UPDATE users 
            SET total_signin_days = total_signin_days + 1
            WHERE id = $1
            """,
            user["id"]
        )
        
        return SigninResponse(
            success=True,
            reward_integral=5,
            reward_tokens=0,
            consecutive_days=0,
            message="补签成功"
        )


@router.post("/repent/buy", response_model=SigninResponse)
async def buy_repent(request: BuyRepentRequest, user = Depends(get_current_user)):
    async with get_db() as conn:
        cost = 100 * request.quantity
        
        user_integral = await conn.fetchval(
            "SELECT integral FROM users WHERE id = $1",
            user["id"]
        )
        
        if user_integral < cost:
            raise HTTPException(status_code=400, detail="积分不足")
        
        await conn.execute(
            "UPDATE users SET integral = integral - $1 WHERE id = $2",
            cost, user["id"]
        )
        
        for _ in range(request.quantity):
            await conn.execute(
                """
                INSERT INTO repent_records (id, user_id, repent_date, created_at)
                VALUES ($1, $2, CURRENT_DATE, NOW())
                """,
                str(uuid.uuid4()), user["id"]
            )
        
        return SigninResponse(
            success=True,
            reward_integral=0,
            reward_tokens=0,
            consecutive_days=0,
            message=f"成功购买{request.quantity}次补签"
        )


@router.get("/tasks", response_model=List[TaskProgressResponse])
async def get_user_tasks(user = Depends(get_current_user)):
    async with get_db() as conn:
        rows = await conn.fetch(
            """
            SELECT t.id, t.name, t.description, t.type, t.target_action, 
                   t.target_count, COALESCE(utp.progress, 0) as current_progress,
                   t.reward_integral, COALESCE(utp.status, 'active') as status
            FROM tasks t
            LEFT JOIN user_task_progress utp ON t.id = utp.task_id AND utp.user_id = $1
            ORDER BY t.type, t.name
            """,
            user["id"]
        )
        
        return [
            TaskProgressResponse(
                task_id=row["id"],
                name=row["name"],
                description=row["description"],
                type=row["type"],
                target_action=row["target_action"],
                target_count=row["target_count"],
                current_progress=row["current_progress"],
                reward_integral=row["reward_integral"],
                status=row["status"]
            )
            for row in rows
        ]


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, user = Depends(get_current_user)):
    async with get_db() as conn:
        task = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1",
            task_id
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        progress = await conn.fetchrow(
            """
            SELECT progress FROM user_task_progress 
            WHERE user_id = $1 AND task_id = $2
            """,
            user["id"], task_id
        )
        
        if not progress:
            await conn.execute(
                """
                INSERT INTO user_task_progress (user_id, task_id, progress, status, last_updated)
                VALUES ($1, $2, 1, 'completed', NOW())
                """,
                user["id"], task_id
            )
        else:
            new_progress = progress["progress"] + 1
            if new_progress >= task["target_count"]:
                await conn.execute(
                    """
                    UPDATE user_task_progress 
                    SET progress = $1, status = 'completed', last_updated = NOW()
                    WHERE user_id = $2 AND task_id = $3
                    """,
                    new_progress, user["id"], task_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE user_task_progress 
                    SET progress = $1, last_updated = NOW()
                    WHERE user_id = $2 AND task_id = $3
                    """,
                    new_progress, user["id"], task_id
                )
        
        if task["reward_integral"] > 0:
            integral_service = IntegralService()
            await integral_service.add_integral(user["id"], task["reward_integral"], f"完成任务: {task['name']}")
        
        return {"success": True, "reward_integral": task["reward_integral"]}


@router.get("/level", response_model=LevelInfoResponse)
async def get_level_info(user = Depends(get_current_user)):
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT level, integral FROM users WHERE id = $1",
            user["id"]
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        current_level = row["level"] or 1
        total_points = row["integral"] or 0
        
        current_level_points = total_points % 1000
        next_level_points = 1000 - current_level_points
        
        benefit_row = await conn.fetchrow(
            "SELECT benefits FROM level_benefits WHERE level = $1",
            current_level
        )
        
        benefits = None
        if benefit_row and benefit_row["benefits"]:
            try:
                benefits = benefit_row["benefits"]
            except:
                pass
        
        return LevelInfoResponse(
            level=current_level,
            total_points=total_points,
            next_level_points=next_level_points,
            current_level_points=current_level_points,
            benefits=benefits
        )


async def init_default_tasks():
    """初始化默认任务数据"""
    async with get_db() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM tasks")
        
        if count > 0:
            return
        
        default_tasks = [
            ("daily_analysis", "每日分析", "每天完成一次房产分析", "daily", "create_task", 1, 10, None, 1),
            ("daily_consult", "咨询达人", "每天咨询3次", "daily", "consult_query", 3, 15, None, 1),
            ("daily_upload", "数据贡献者", "每天上传一条数据", "daily", "upload_data", 1, 20, None, 1),
            ("weekly_active", "周活跃", "一周完成7次分析", "weekly", "create_task", 7, 100, None, 7),
            ("weekly_invite", "邀请好友", "邀请一位新用户注册", "weekly", "invite_user", 1, 200, None, 7),
            ("achievement_signin7", "连续签到7天", "连续签到7天", "achievement", "signin_consecutive", 7, 500, '{"badge": "signin_master_7"}', 0),
            ("achievement_first_upload", "首次上传", "首次上传数据", "achievement", "upload_data", 1, 50, '{"badge": "first_contributor"}', 0),
        ]
        
        for task in default_tasks:
            task_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO tasks (id, name, description, type, target_action, target_count, reward_integral, extra_reward, frequency)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                task_id, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8]
            )
        
        default_levels = [
            (1, 0, '{"title": "新手", "benefits": ["基础功能"]}', "/icons/level1.png"),
            (2, 1000, '{"title": "入门", "benefits": ["基础功能", "每日任务奖励+5%"]}', "/icons/level2.png"),
            (3, 2000, '{"title": "熟练", "benefits": ["基础功能", "每日任务奖励+10%", "专属客服"]}', "/icons/level3.png"),
            (4, 5000, '{"title": "专家", "benefits": ["基础功能", "每日任务奖励+15%", "专属客服", "报告去水印"]}', "/icons/level4.png"),
            (5, 10000, '{"title": "大师", "benefits": ["基础功能", "每日任务奖励+20%", "专属客服", "报告去水印", "优先支持"]}', "/icons/level5.png"),
        ]
        
        for level in default_levels:
            await conn.execute(
                """
                INSERT INTO level_benefits (level, required_points, benefits, icon)
                VALUES ($1, $2, $3, $4)
                """,
                level[0], level[1], level[2], level[3]
            )
        
        logger.info("默认任务和等级数据初始化完成")


async def reset_daily_tasks():
    """重置每日任务"""
    async with get_db() as conn:
        daily_task_ids = await conn.fetch(
            "SELECT id FROM tasks WHERE type = 'daily'"
        )
        
        for task_id in daily_task_ids:
            await conn.execute(
                """
                UPDATE user_task_progress 
                SET progress = 0, status = 'active', last_updated = NOW()
                WHERE task_id = $1
                """,
                task_id["id"]
            )
        
        logger.info("每日任务已重置")


async def reset_weekly_tasks():
    """重置每周任务"""
    async with get_db() as conn:
        weekly_task_ids = await conn.fetch(
            "SELECT id FROM tasks WHERE type = 'weekly'"
        )
        
        for task_id in weekly_task_ids:
            await conn.execute(
                """
                UPDATE user_task_progress 
                SET progress = 0, status = 'active', last_updated = NOW()
                WHERE task_id = $1
                """,
                task_id["id"]
            )
        
        logger.info("每周任务已重置")
