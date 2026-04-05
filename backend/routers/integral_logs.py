"""
积分日志查询接口
用户端和管理员端积分日志查询
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import csv
import io
from fastapi.responses import StreamingResponse
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api", tags=["积分日志"])

TOKEN_MULTIPLIER = 100


class IntegralLogItem(BaseModel):
    id: str
    change: float
    balance_after: float
    token_change: int
    token_balance_after: int
    reason: str
    action_type: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    created_at: str


class IntegralLogsResponse(BaseModel):
    logs: List[IntegralLogItem]
    total: int
    page: int
    limit: int
    total_pages: int


class IntegralBalanceResponse(BaseModel):
    integral: float
    tokens: int
    today_earned: float
    today_consumed: float
    total_earned: float
    total_consumed: float


class IntegralStatsResponse(BaseModel):
    total_earned: float
    total_consumed: float
    earn_count: int
    consume_count: int
    signin_count: int
    task_count: int


@router.get("/user/integral/balance", response_model=IntegralBalanceResponse)
async def get_user_integral_balance(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        user = await cursor.fetchone()
        integral = user['integral'] if user else 0
        tokens = int(integral * TOKEN_MULTIPLIER)
        
        today = date.today().isoformat()
        await cursor.execute('''
            SELECT 
                SUM(CASE WHEN change > 0 AND created_at >= ? THEN change ELSE 0 END) as today_earned,
                SUM(CASE WHEN change < 0 AND created_at >= ? THEN ABS(change) ELSE 0 END) as today_consumed
            FROM integral_logs WHERE user_id = ?
        ''', (today, today, user_id))
        today_stats = await cursor.fetchone()
        
        await cursor.execute('''
            SELECT 
                SUM(CASE WHEN change > 0 THEN change ELSE 0 END) as total_earned,
                SUM(CASE WHEN change < 0 THEN ABS(change) ELSE 0 END) as total_consumed
            FROM integral_logs WHERE user_id = ?
        ''', (user_id,))
        total_stats = await cursor.fetchone()
        
        return IntegralBalanceResponse(
            integral=integral,
            tokens=tokens,
            today_earned=today_stats['today_earned'] or 0,
            today_consumed=today_stats['today_consumed'] or 0,
            total_earned=total_stats['total_earned'] or 0,
            total_consumed=total_stats['total_consumed'] or 0
        )


@router.get("/user/integral/logs", response_model=IntegralLogsResponse)
async def get_user_integral_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        where_clauses = ['user_id = ?']
        params = [user_id]
        
        if start_date:
            where_clauses.append('created_at >= ?')
            params.append(start_date)
        if end_date:
            where_clauses.append('created_at <= ?')
            params.append(end_date + ' 23:59:59')
        if action_type:
            where_clauses.append('action_type = ?')
            params.append(action_type)
        
        where_sql = ' AND '.join(where_clauses)
        
        await cursor.execute(f'SELECT COUNT(*) as total FROM integral_logs WHERE {where_sql}', params)
        total = (await cursor.fetchone())['total']
        
        offset = (page - 1) * limit
        await cursor.execute(f'''
            SELECT * FROM integral_logs 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        rows = await cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append(IntegralLogItem(
                id=row['id'],
                change=row['change'],
                balance_after=row['balance_after'],
                token_change=int(row['change'] * TOKEN_MULTIPLIER),
                token_balance_after=int(row['balance_after'] * TOKEN_MULTIPLIER),
                reason=row['reason'],
                action_type=row['action_type'],
                resource_id=row['resource_id'],
                resource_type=row['resource_type'],
                created_at=row['created_at']
            ))
        
        total_pages = (total + limit - 1) // limit
        
        return IntegralLogsResponse(
            logs=logs,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )


@router.get("/user/integral/stats", response_model=IntegralStatsResponse)
async def get_user_integral_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute('''
            SELECT 
                SUM(CASE WHEN change > 0 THEN change ELSE 0 END) as total_earned,
                SUM(CASE WHEN change < 0 THEN ABS(change) ELSE 0 END) as total_consumed,
                COUNT(CASE WHEN change > 0 THEN 1 END) as earn_count,
                COUNT(CASE WHEN change < 0 THEN 1 END) as consume_count,
                COUNT(CASE WHEN action_type = 'signin' THEN 1 END) as signin_count,
                COUNT(CASE WHEN action_type = 'task_create' THEN 1 END) as task_count
            FROM integral_logs WHERE user_id = ?
        ''', (user_id,))
        stats = await cursor.fetchone()
        
        return IntegralStatsResponse(
            total_earned=stats['total_earned'] or 0,
            total_consumed=stats['total_consumed'] or 0,
            earn_count=stats['earn_count'] or 0,
            consume_count=stats['consume_count'] or 0,
            signin_count=stats['signin_count'] or 0,
            task_count=stats['task_count'] or 0
        )


@router.get("/user/integral/logs/export")
async def export_user_integral_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        where_clauses = ['user_id = ?']
        params = [user_id]
        
        if start_date:
            where_clauses.append('created_at >= ?')
            params.append(start_date)
        if end_date:
            where_clauses.append('created_at <= ?')
            params.append(end_date + ' 23:59:59')
        if action_type:
            where_clauses.append('action_type = ?')
            params.append(action_type)
        
        where_sql = ' AND '.join(where_clauses)
        
        await cursor.execute(f'''
            SELECT * FROM integral_logs 
            WHERE {where_sql}
            ORDER BY created_at DESC
        ''', params)
        rows = await cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['时间', '变动', '变动后余额', 'Token变动', 'Token余额', '原因', '类型'])
        
        for row in rows:
            writer.writerow([
                row['created_at'],
                row['change'],
                row['balance_after'],
                int(row['change'] * TOKEN_MULTIPLIER),
                int(row['balance_after'] * TOKEN_MULTIPLIER),
                row['reason'],
                row['action_type'] or ''
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=integral_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
        )


@router.get("/user/integral/action-types")
async def get_integral_action_types():
    return {
        "types": [
            {"value": "signin", "label": "签到奖励"},
            {"value": "makeup_signin", "label": "补签奖励"},
            {"value": "task_create", "label": "任务消耗"},
            {"value": "task_reward", "label": "任务奖励"},
            {"value": "recharge", "label": "充值"},
            {"value": "admin_add", "label": "管理员增加"},
            {"value": "admin_deduct", "label": "管理员扣除"},
            {"value": "consult", "label": "咨询消耗"},
            {"value": "export", "label": "导出消耗"},
            {"value": "reward", "label": "系统奖励"},
            {"value": "register", "label": "注册赠送"},
            {"value": "admin_adjust", "label": "管理员调整"},
        ]
    }
