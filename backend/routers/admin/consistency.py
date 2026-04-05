"""
数据一致性检查与修复API
提供管理员接口检查和修复数据一致性
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from backend.auth import get_current_user, require_admin
from backend.database import get_db_connection
from backend.event_bus import event_bus

router = APIRouter(prefix="/api/admin/consistency", tags=["consistency"])


class ConsistencyCheckResult(BaseModel):
    check_type: str
    expected: int
    actual: int
    is_consistent: bool
    details: Optional[str] = None


class ConsistencyReport(BaseModel):
    total_users: int
    source_stats_sum: int
    city_stats_sum: int
    district_stats_sum: int
    behavior_stats_count: int
    is_consistent: bool
    checks: List[ConsistencyCheckResult]
    checked_at: str


class RebuildResult(BaseModel):
    success: bool
    message: str
    details: Dict


@router.get("/check", response_model=ConsistencyReport)
async def check_consistency(current_user: dict = Depends(require_admin)):
    """
    检查系统数据一致性
    
    比较用户总数与各统计表的总和
    """
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COALESCE(SUM(user_count), 0) FROM user_source_stats")
        source_stats_sum = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COALESCE(SUM(user_count), 0) FROM user_city_stats")
        city_stats_sum = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COALESCE(SUM(user_count), 0) FROM user_district_stats")
        district_stats_sum = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM user_behavior_stats")
        behavior_stats_count = (await cursor.fetchone())[0]
        
        checks = []
        
        cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE source IS NOT NULL AND source != ''")
        users_with_source = (await cursor.fetchone())[0]
        checks.append(ConsistencyCheckResult(
            check_type="source_stats",
            expected=users_with_source,
            actual=source_stats_sum,
            is_consistent=users_with_source == source_stats_sum,
            details=f"Users with source: {users_with_source}, Source stats sum: {source_stats_sum}"
        ))
        
        cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE city IS NOT NULL AND city != ''")
        users_with_city = (await cursor.fetchone())[0]
        checks.append(ConsistencyCheckResult(
            check_type="city_stats",
            expected=users_with_city,
            actual=city_stats_sum,
            is_consistent=users_with_city == city_stats_sum,
            details=f"Users with city: {users_with_city}, City stats sum: {city_stats_sum}"
        ))
        
        cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE city IS NOT NULL AND city != '' AND district IS NOT NULL AND district != ''")
        users_with_district = (await cursor.fetchone())[0]
        checks.append(ConsistencyCheckResult(
            check_type="district_stats",
            expected=users_with_district,
            actual=district_stats_sum,
            is_consistent=users_with_district == district_stats_sum,
            details=f"Users with district: {users_with_district}, District stats sum: {district_stats_sum}"
        ))
        
        checks.append(ConsistencyCheckResult(
            check_type="behavior_stats",
            expected=total_users,
            actual=behavior_stats_count,
            is_consistent=total_users == behavior_stats_count,
            details=f"Total users: {total_users}, Behavior stats: {behavior_stats_count}"
        ))
        
        is_consistent = all(c.is_consistent for c in checks)
        
        log_id = str(uuid.uuid4())
        await conn.execute('''
            INSERT INTO consistency_logs (id, check_type, expected_value, actual_value, is_consistent, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (log_id, 'full_check', total_users, source_stats_sum, 1 if is_consistent else 0, str([c.dict() for c in checks])))
        await conn.commit()
        
    finally:
        await conn.close()
    
    return ConsistencyReport(
        total_users=total_users,
        source_stats_sum=source_stats_sum,
        city_stats_sum=city_stats_sum,
        district_stats_sum=district_stats_sum,
        behavior_stats_count=behavior_stats_count,
        is_consistent=is_consistent,
        checks=checks,
        checked_at=datetime.now().isoformat()
    )


@router.post("/rebuild", response_model=RebuildResult)
async def rebuild_stats(current_user: dict = Depends(require_admin)):
    """
    重建所有统计表
    
    从原始用户数据重新聚合统计数据
    """
    conn = await get_db_connection()
    
    try:
        await conn.execute("DELETE FROM user_source_stats")
        await conn.execute('''
            INSERT INTO user_source_stats (source, user_count, updated_at)
            SELECT 
                COALESCE(source, 'unknown') as source,
                COUNT(*) as user_count,
                CURRENT_TIMESTAMP
            FROM users
            GROUP BY COALESCE(source, 'unknown')
        ''')
        
        await conn.execute("DELETE FROM user_city_stats")
        await conn.execute('''
            INSERT INTO user_city_stats (city, user_count, updated_at)
            SELECT 
                city,
                COUNT(*) as user_count,
                CURRENT_TIMESTAMP
            FROM users
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city
        ''')
        
        await conn.execute("DELETE FROM user_district_stats")
        await conn.execute('''
            INSERT INTO user_district_stats (id, city, district, user_count, updated_at)
            SELECT 
                city || '_' || district as id,
                city,
                district,
                COUNT(*) as user_count,
                CURRENT_TIMESTAMP
            FROM users
            WHERE city IS NOT NULL AND city != '' AND district IS NOT NULL AND district != ''
            GROUP BY city, district
        ''')
        
        await conn.execute("DELETE FROM user_behavior_stats")
        await conn.execute('''
            INSERT INTO user_behavior_stats (user_id, total_tasks, completed_tasks, updated_at)
            SELECT 
                u.id as user_id,
                COALESCE(t.total_tasks, 0) as total_tasks,
                COALESCE(t.completed_tasks, 0) as completed_tasks,
                CURRENT_TIMESTAMP
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as total_tasks, 
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM analysis_tasks
                GROUP BY user_id
            ) t ON u.id = t.user_id
        ''')
        
        cursor = await conn.execute("SELECT COUNT(*) FROM user_source_stats")
        source_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM user_city_stats")
        city_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM user_district_stats")
        district_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM user_behavior_stats")
        behavior_count = (await cursor.fetchone())[0]
        
        await conn.commit()
        
    except Exception as e:
        await conn.rollback()
        raise HTTPException(status_code=500, detail=f"重建失败: {str(e)}")
    finally:
        await conn.close()
    
    return RebuildResult(
        success=True,
        message="统计数据重建完成",
        details={
            "source_stats": source_count,
            "city_stats": city_count,
            "district_stats": district_count,
            "behavior_stats": behavior_count
        }
    )


@router.get("/logs")
async def get_consistency_logs(
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """获取一致性检查日志"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT * FROM consistency_logs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        logs = await cursor.fetchall()
        
        return {
            "logs": [dict(log) for log in logs],
            "total": len(logs)
        }
    finally:
        await conn.close()


@router.get("/source-stats")
async def get_source_stats(current_user: dict = Depends(require_admin)):
    """获取来源统计详情"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT source, user_count, updated_at
            FROM user_source_stats
            ORDER BY user_count DESC
        ''')
        stats = await cursor.fetchall()
        
        return {
            "stats": [dict(s) for s in stats],
            "total_sources": len(stats)
        }
    finally:
        await conn.close()


@router.get("/city-stats")
async def get_city_stats(current_user: dict = Depends(require_admin)):
    """获取城市统计详情"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT city, user_count, updated_at
            FROM user_city_stats
            ORDER BY user_count DESC
        ''')
        stats = await cursor.fetchall()
        
        return {
            "stats": [dict(s) for s in stats],
            "total_cities": len(stats)
        }
    finally:
        await conn.close()


@router.get("/district-stats")
async def get_district_stats(
    city: str = None,
    current_user: dict = Depends(require_admin)
):
    """获取区域统计详情"""
    conn = await get_db_connection()
    
    try:
        if city:
            cursor = await conn.execute('''
                SELECT city, district, user_count, updated_at
                FROM user_district_stats
                WHERE city = ?
                ORDER BY user_count DESC
            ''', (city,))
        else:
            cursor = await conn.execute('''
                SELECT city, district, user_count, updated_at
                FROM user_district_stats
                ORDER BY user_count DESC
            ''')
        stats = await cursor.fetchall()
        
        return {
            "stats": [dict(s) for s in stats],
            "total_districts": len(stats)
        }
    finally:
        await conn.close()
