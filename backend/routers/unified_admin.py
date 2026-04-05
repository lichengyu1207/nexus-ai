"""
统一管理面板 - 综合API路由
整合用户、智能体、任务、积分、记忆、系统配置等管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from backend.auth import get_current_user
from backend.database_pg import get_db

router = APIRouter(prefix="/api/admin/unified", tags=["统一管理面板"])


class AdminLogMiddleware:
    @staticmethod
    async def log_operation(
        admin_id: str,
        operation_type: str,
        target_type: str = None,
        target_id: str = None,
        before_data: dict = None,
        after_data: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        async with get_db() as db:
            await db.execute("""
                INSERT INTO admin_operation_logs 
                (id, admin_id, operation_type, target_type, target_id, 
                 before_data, after_data, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                str(uuid.uuid4()),
                admin_id,
                operation_type,
                target_type,
                target_id,
                json.dumps(before_data, ensure_ascii=False) if before_data else None,
                json.dumps(after_data, ensure_ascii=False) if after_data else None,
                ip_address,
                user_agent
            )


async def require_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    role = current_user.get("role", "user")
    is_admin = current_user.get("is_admin", False)
    
    if role not in ["admin", "super_admin"] and not is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return current_user


async def require_super_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    role = current_user.get("role", "user")
    
    if role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    
    return current_user


def get_client_info(request: Request):
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


@router.get("/dashboard/stats")
async def get_unified_dashboard_stats(
    admin: dict = Depends(require_admin_user)
):
    stats = {}
    
    async with get_db() as db:
        users_count = await db.fetchone("SELECT COUNT(*) as count FROM users")
        stats["total_users"] = users_count[0] if users_count else 0
        
        today_users = await db.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = CURRENT_DATE"
        )
        stats["new_users_today"] = today_users[0] if today_users else 0
        
        week_users = await db.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
        )
        stats["new_users_week"] = week_users[0] if week_users else 0
        
        agents_count = await db.fetchone("SELECT COUNT(*) as count FROM user_agents")
        stats["total_agents"] = agents_count[0] if agents_count else 0
        
        tasks_count = await db.fetchone("SELECT COUNT(*) as count FROM analysis_tasks")
        stats["total_tasks"] = tasks_count[0] if tasks_count else 0
        
        completed_tasks = await db.fetchone(
            "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'completed'"
        )
        stats["completed_tasks"] = completed_tasks[0] if completed_tasks else 0
        
        auto_tasks = await db.fetchone("SELECT COUNT(*) as count FROM auto_tasks")
        stats["auto_tasks"] = auto_tasks[0] if auto_tasks else 0
        
        memories_count = await db.fetchone("SELECT COUNT(*) as count FROM hippocampus_memories")
        stats["total_memories"] = memories_count[0] if memories_count else 0
        
        integral_total = await db.fetchone(
            "SELECT COALESCE(SUM(integral), 0) as total FROM users"
        )
        stats["total_integral"] = integral_total[0] if integral_total else 0
        
        integral_logs_today = await db.fetchone(
            "SELECT COUNT(*) as count FROM integral_logs WHERE DATE(created_at) = CURRENT_DATE"
        )
        stats["integral_logs_today"] = integral_logs_today[0] if integral_logs_today else 0
        
        user_growth = await db.fetch("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        stats["user_growth"] = [
            {"date": str(row[0]), "count": row[1]} 
            for row in user_growth
        ]
        
        task_trend = await db.fetch("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM analysis_tasks
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        stats["task_trend"] = [
            {"date": str(row[0]), "count": row[1]} 
            for row in task_trend
        ]
        
        agent_by_dept = await db.fetch("""
            SELECT department, COUNT(*) as count
            FROM user_agents
            GROUP BY department
        """)
        stats["agents_by_department"] = {row[0]: row[1] for row in agent_by_dept}
        
        memory_by_type = await db.fetch("""
            SELECT type, COUNT(*) as count
            FROM hippocampus_memories
            GROUP BY type
        """)
        stats["memories_by_type"] = {row[0]: row[1] for row in memory_by_type}
    
    return stats


@router.get("/users")
async def list_users_unified(
    search: str = Query(None),
    role: str = Query(None),
    is_active: bool = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if search:
            conditions.append(f"(email ILIKE ${param_idx} OR username ILIKE ${param_idx} OR full_name ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1
        
        if role:
            conditions.append(f"role = ${param_idx}")
            params.append(role)
            param_idx += 1
        
        if is_active is not None:
            conditions.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM users WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT id, email, username, full_name, role, is_admin, is_active, 
                   integral, created_at, last_login
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "email": row[1],
                "username": row[2],
                "full_name": row[3],
                "role": row[4],
                "is_admin": row[5],
                "is_active": row[6],
                "integral": row[7],
                "created_at": str(row[8]) if row[8] else None,
                "last_login": str(row[9]) if row[9] else None,
            })
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }


@router.get("/users/{user_id}")
async def get_user_detail_unified(
    user_id: str,
    admin: dict = Depends(require_admin_user)
):
    async with get_db() as db:
        user_row = await db.fetchone("""
            SELECT id, email, username, full_name, role, is_admin, is_active,
                   integral, created_at, last_login, avatar_url
            FROM users WHERE id = $1
        """, user_id)
        
        if not user_row:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        agents = await db.fetch("""
            SELECT id, name, department, level, status, created_at
            FROM user_agents WHERE user_id = $1
        """, user_id)
        
        tasks = await db.fetch("""
            SELECT id, type, status, created_at
            FROM analysis_tasks WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 10
        """, user_id)
        
        integral_logs = await db.fetch("""
            SELECT id, type, amount, balance, description, created_at
            FROM integral_logs WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 10
        """, user_id)
        
        memories = await db.fetch("""
            SELECT id, type, summary, importance, created_at
            FROM hippocampus_memories WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 10
        """, user_id)
        
        return {
            "user": {
                "id": user_row[0],
                "email": user_row[1],
                "username": user_row[2],
                "full_name": user_row[3],
                "role": user_row[4],
                "is_admin": user_row[5],
                "is_active": user_row[6],
                "integral": user_row[7],
                "created_at": str(user_row[8]) if user_row[8] else None,
                "last_login": str(user_row[9]) if user_row[9] else None,
                "avatar_url": user_row[10],
            },
            "agents": [{"id": a[0], "name": a[1], "department": a[2], "level": a[3], "status": a[4], "created_at": str(a[5]) if a[5] else None} for a in agents],
            "tasks": [{"id": t[0], "type": t[1], "status": t[2], "created_at": str(t[3]) if t[3] else None} for t in tasks],
            "integral_logs": [{"id": l[0], "type": l[1], "amount": l[2], "balance": l[3], "description": l[4], "created_at": str(l[5]) if l[5] else None} for l in integral_logs],
            "memories": [{"id": m[0], "type": m[1], "summary": m[2], "importance": m[3], "created_at": str(m[4]) if m[4] else None} for m in memories],
        }


@router.post("/users/{user_id}/adjust-integral")
async def adjust_user_integral(
    user_id: str,
    amount: int = Query(..., description="积分变动量（正数增加，负数减少）"),
    reason: str = Query(..., description="调整原因"),
    request: Request = None,
    admin: dict = Depends(require_admin_user)
):
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    async with get_db() as db:
        user = await db.fetchone("SELECT id, integral FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_integral = user[1] or 0
        new_integral = old_integral + amount
        
        if new_integral < 0:
            raise HTTPException(status_code=400, detail="积分不能为负数")
        
        await db.execute(
            "UPDATE users SET integral = $1 WHERE id = $2",
            new_integral, user_id
        )
        
        await db.execute("""
            INSERT INTO integral_logs (id, user_id, type, amount, balance, description)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, str(uuid.uuid4()), user_id, "admin_adjust", amount, new_integral, f"管理员调整: {reason}")
        
        await AdminLogMiddleware.log_operation(
            admin_id=admin["id"],
            operation_type="integral_adjust",
            target_type="user",
            target_id=user_id,
            before_data={"integral": old_integral},
            after_data={"integral": new_integral, "amount": amount, "reason": reason},
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "old_integral": old_integral,
            "new_integral": new_integral,
            "amount": amount
        }


@router.get("/agents")
async def list_agents_unified(
    department: str = Query(None),
    user_id: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if department:
            conditions.append(f"department = ${param_idx}")
            params.append(department)
            param_idx += 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM user_agents WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT ua.id, ua.user_id, ua.name, ua.department, ua.level, ua.status,
                   ua.created_at, u.email as user_email
            FROM user_agents ua
            LEFT JOIN users u ON ua.user_id = u.id
            WHERE {where_clause}
            ORDER BY ua.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        agents = []
        for row in rows:
            agents.append({
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "department": row[3],
                "level": row[4],
                "status": row[5],
                "created_at": str(row[6]) if row[6] else None,
                "user_email": row[7],
            })
        
        return {
            "agents": agents,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.get("/tasks")
async def list_tasks_unified(
    task_type: str = Query(None),
    status: str = Query(None),
    user_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if task_type:
            conditions.append(f"type = ${param_idx}")
            params.append(task_type)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM analysis_tasks WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT id, user_id, type, status, created_at, completed_at
            FROM analysis_tasks
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "user_id": row[1],
                "type": row[2],
                "status": row[3],
                "created_at": str(row[4]) if row[4] else None,
                "completed_at": str(row[5]) if row[5] else None,
            })
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.get("/integral/logs")
async def list_integral_logs_unified(
    user_id: str = Query(None),
    log_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if log_type:
            conditions.append(f"type = ${param_idx}")
            params.append(log_type)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM integral_logs WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT il.id, il.user_id, il.type, il.amount, il.balance, 
                   il.description, il.created_at, u.email as user_email
            FROM integral_logs il
            LEFT JOIN users u ON il.user_id = u.id
            WHERE {where_clause}
            ORDER BY il.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "type": row[2],
                "amount": row[3],
                "balance": row[4],
                "description": row[5],
                "created_at": str(row[6]) if row[6] else None,
                "user_email": row[7],
            })
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.post("/integral/batch-issue")
async def batch_issue_integral(
    user_ids: List[str] = None,
    amount: int = Query(..., ge=1),
    reason: str = Query(...),
    request: Request = None,
    admin: dict = Depends(require_super_admin_user)
):
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    if not user_ids:
        raise HTTPException(status_code=400, detail="请提供用户ID列表")
    
    results = []
    
    async with get_db() as db:
        for user_id in user_ids:
            user = await db.fetchone("SELECT id, integral FROM users WHERE id = $1", user_id)
            if not user:
                results.append({"user_id": user_id, "success": False, "error": "用户不存在"})
                continue
            
            old_integral = user[1] or 0
            new_integral = old_integral + amount
            
            await db.execute(
                "UPDATE users SET integral = $1 WHERE id = $2",
                new_integral, user_id
            )
            
            await db.execute("""
                INSERT INTO integral_logs (id, user_id, type, amount, balance, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, str(uuid.uuid4()), user_id, "admin_batch", amount, new_integral, reason)
            
            results.append({"user_id": user_id, "success": True, "new_integral": new_integral})
        
        await AdminLogMiddleware.log_operation(
            admin_id=admin["id"],
            operation_type="integral_batch_issue",
            target_type="users",
            before_data={},
            after_data={"user_count": len(user_ids), "amount": amount, "reason": reason},
            ip_address=ip,
            user_agent=user_agent
        )
    
    return {
        "success": True,
        "processed_count": len([r for r in results if r["success"]]),
        "failed_count": len([r for r in results if not r["success"]]),
        "results": results
    }


@router.get("/memories")
async def list_memories_unified(
    user_id: str = Query(None),
    memory_type: str = Query(None),
    min_importance: float = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if memory_type:
            conditions.append(f"type = ${param_idx}")
            params.append(memory_type)
            param_idx += 1
        
        if min_importance is not None:
            conditions.append(f"importance >= ${param_idx}")
            params.append(min_importance)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM hippocampus_memories WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT hm.id, hm.user_id, hm.type, hm.summary, hm.importance,
                   hm.source, hm.created_at, u.email as user_email
            FROM hippocampus_memories hm
            LEFT JOIN users u ON hm.user_id = u.id
            WHERE {where_clause}
            ORDER BY hm.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "user_id": row[1],
                "type": row[2],
                "summary": row[3],
                "importance": row[4],
                "source": row[5],
                "created_at": str(row[6]) if row[6] else None,
                "user_email": row[7],
            })
        
        return {
            "memories": memories,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.delete("/memories/{memory_id}")
async def delete_memory_unified(
    memory_id: str,
    request: Request = None,
    admin: dict = Depends(require_admin_user)
):
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    async with get_db() as db:
        memory = await db.fetchone(
            "SELECT id, user_id, summary FROM hippocampus_memories WHERE id = $1",
            memory_id
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        
        await db.execute("DELETE FROM memory_entity_map WHERE memory_id = $1", memory_id)
        await db.execute("DELETE FROM memory_relations WHERE memory_id1 = $1 OR memory_id2 = $1", memory_id)
        await db.execute("DELETE FROM hippocampus_memories WHERE id = $1", memory_id)
        
        await AdminLogMiddleware.log_operation(
            admin_id=admin["id"],
            operation_type="memory_delete",
            target_type="memory",
            target_id=memory_id,
            before_data={"user_id": memory[1], "summary": memory[2]},
            after_data={},
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {"success": True, "message": "记忆已删除"}


@router.get("/configs")
async def get_system_configs(
    group: str = Query(None, description="配置分组"),
    admin: dict = Depends(require_admin_user)
):
    async with get_db() as db:
        if group:
            rows = await db.fetch(
                "SELECT key, value, description, updated_at FROM system_configs WHERE key LIKE $1",
                f"{group}%"
            )
        else:
            rows = await db.fetch(
                "SELECT key, value, description, updated_at FROM system_configs"
            )
        
        configs = {}
        for row in rows:
            key = row[0]
            value = row[1]
            try:
                value = json.loads(value)
            except:
                pass
            
            configs[key] = {
                "value": value,
                "description": row[2],
                "updated_at": str(row[3]) if row[3] else None
            }
        
        return {"configs": configs}


@router.put("/configs/{key}")
async def update_system_config(
    key: str,
    value: Dict[str, Any] = None,
    request: Request = None,
    admin: dict = Depends(require_super_admin_user)
):
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    async with get_db() as db:
        existing = await db.fetchone(
            "SELECT value FROM system_configs WHERE key = $1",
            key
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="配置项不存在")
        
        old_value = existing[0]
        new_value = json.dumps(value, ensure_ascii=False) if value else None
        
        await db.execute("""
            UPDATE system_configs 
            SET value = $1, updated_at = CURRENT_TIMESTAMP, updated_by = $2
            WHERE key = $3
        """, new_value, admin["id"], key)
        
        await AdminLogMiddleware.log_operation(
            admin_id=admin["id"],
            operation_type="config_update",
            target_type="config",
            target_id=key,
            before_data={"value": old_value},
            after_data={"value": new_value},
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {"success": True, "key": key}


@router.get("/audit-logs")
async def list_audit_logs(
    admin_id: str = Query(None),
    operation_type: str = Query(None),
    target_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin_user)
):
    offset = (page - 1) * page_size
    
    async with get_db() as db:
        conditions = []
        params = []
        param_idx = 1
        
        if admin_id:
            conditions.append(f"admin_id = ${param_idx}")
            params.append(admin_id)
            param_idx += 1
        
        if operation_type:
            conditions.append(f"operation_type = ${param_idx}")
            params.append(operation_type)
            param_idx += 1
        
        if target_type:
            conditions.append(f"target_type = ${param_idx}")
            params.append(target_type)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_row = await db.fetchone(
            f"SELECT COUNT(*) FROM admin_operation_logs WHERE {where_clause}",
            *params
        )
        total = count_row[0] if count_row else 0
        
        params.extend([page_size, offset])
        rows = await db.fetch(f"""
            SELECT al.id, al.admin_id, al.operation_type, al.target_type,
                   al.target_id, al.before_data, al.after_data, al.ip_address,
                   al.created_at, u.email as admin_email
            FROM admin_operation_logs al
            LEFT JOIN users u ON al.admin_id = u.id
            WHERE {where_clause}
            ORDER BY al.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params)
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "admin_id": row[1],
                "operation_type": row[2],
                "target_type": row[3],
                "target_id": row[4],
                "before_data": row[5],
                "after_data": row[6],
                "ip_address": row[7],
                "created_at": str(row[8]) if row[8] else None,
                "admin_email": row[9],
            })
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.get("/market/stats")
async def get_market_stats(
    admin: dict = Depends(require_admin_user)
):
    async with get_db() as db:
        total_recruits = await db.fetchone(
            "SELECT COUNT(*) FROM agent_recruit_logs"
        )
        
        by_rarity = await db.fetch("""
            SELECT rarity, COUNT(*) as count
            FROM user_agents
            GROUP BY rarity
        """)
        
        recent_recruits = await db.fetch("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM agent_recruit_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        return {
            "total_recruits": total_recruits[0] if total_recruits else 0,
            "by_rarity": {row[0]: row[1] for row in by_rarity},
            "recent_trend": [{"date": str(row[0]), "count": row[1]} for row in recent_recruits]
        }
