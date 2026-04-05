"""
智能体监控仪表盘与任务分配API
Agent Monitoring Dashboard and Task Assignment API

提供智能体实时状态、任务监控、任务分配等功能
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import get_db_connection
from ..logger import get_logger

logger = get_logger("agent_dashboard")

router = APIRouter(prefix="/api/dashboard", tags=["agent-dashboard"])


class AgentStatus(BaseModel):
    id: str
    name: str
    department: str
    status: str
    current_task: Optional[str] = None
    current_task_id: Optional[str] = None
    efficiency: float = 1.0
    level: int = 1
    work_time_seconds: int = 0
    performance_today: int = 0
    avatar: Optional[str] = None


class TaskInfo(BaseModel):
    id: str
    type: str
    description: str
    status: str
    progress: float
    assigned_agents: List[Dict[str, str]]
    start_time: str
    estimated_end_time: Optional[str] = None


class TaskStartRequest(BaseModel):
    task_type: str
    input: str
    auto_assign: bool = True
    agent_ids: Optional[List[str]] = None


class AgentRecommendation(BaseModel):
    agent_id: str
    agent_name: str
    department: str
    score: float
    reason: str


@dataclass
class ConnectionManager:
    active_connections: List[WebSocket] = None
    
    def __post_init__(self):
        if self.active_connections is None:
            self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@router.get("/agents-status")
async def get_agents_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前用户所有智能体的实时状态
    """
    user_id = current_user["id"]
    agents = []
    
    async for conn in get_db_connection():
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_agents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    agent_template_id TEXT,
                    name TEXT,
                    department TEXT,
                    level INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'idle',
                    current_task_id TEXT,
                    current_task_type TEXT,
                    work_start_time TIMESTAMP,
                    performance_today INTEGER DEFAULT 0,
                    efficiency REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor = await conn.execute("""
                SELECT id, name, department, status, current_task_id, 
                       current_task_type, efficiency, level, work_start_time,
                       performance_today
                FROM user_agents
                WHERE user_id = ?
            """, (user_id,))
            
            rows = await cursor.fetchall()
            
            for row in rows:
                work_time = 0
                if row[8]:
                    try:
                        start = datetime.fromisoformat(str(row[8]).replace('Z', '+00:00'))
                        work_time = int((datetime.now() - start.replace(tzinfo=None)).total_seconds())
                    except:
                        pass
                
                current_task = None
                if row[4]:
                    current_task = await _get_task_description(conn, row[4], row[5])
                
                agents.append(AgentStatus(
                    id=row[0],
                    name=row[1] or f"智能体_{row[0][:8]}",
                    department=row[2] or "未分配",
                    status=row[3] or "idle",
                    current_task=current_task,
                    current_task_id=row[4],
                    efficiency=row[6] or 1.0,
                    level=row[7] or 1,
                    work_time_seconds=work_time,
                    performance_today=row[9] or 0
                ))
            
            break
        finally:
            await conn.close()
    
    if not agents:
        agents = await _get_default_agents(user_id)
    
    return {
        "agents": [a.dict() for a in agents],
        "total": len(agents),
        "idle_count": sum(1 for a in agents if a.status == "idle"),
        "busy_count": sum(1 for a in agents if a.status == "busy"),
        "auto_count": sum(1 for a in agents if a.status == "auto"),
    }


async def _get_task_description(conn, task_id: str, task_type: str) -> str:
    if task_type == "user_task":
        cursor = await conn.execute("""
            SELECT task_type, input FROM user_tasks WHERE id = ?
        """, (task_id,))
        row = await cursor.fetchone()
        if row:
            return f"{row[0]}: {row[1][:30]}..." if row[1] else row[0]
    elif task_type == "auto_task":
        cursor = await conn.execute("""
            SELECT task_type, description FROM auto_tasks WHERE id = ?
        """, (task_id,))
        row = await cursor.fetchone()
        if row:
            return f"自主任务: {row[1][:30]}..." if row[1] else "自主任务"
    return "执行中"


async def _get_default_agents(user_id: str) -> List[AgentStatus]:
    departments = [
        ("吏部", "li", "用户管理与权限"),
        ("户部", "hu", "数据统计与积分"),
        ("礼部", "li_guan", "用户交互与咨询"),
        ("兵部", "bing", "数据采集与爬虫"),
        ("刑部", "xing", "安全审计与防御"),
        ("工部", "gong", "报告生成与分析"),
    ]
    
    agents = []
    for name, dept, desc in departments:
        agents.append(AgentStatus(
            id=f"{dept}_agent",
            name=name,
            department=dept,
            status="idle",
            efficiency=1.0,
            level=1
        ))
    
    return agents


@router.get("/current-tasks")
async def get_current_tasks(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前进行中的任务列表
    """
    user_id = current_user["id"]
    tasks = []
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT id, task_type, input, status, created_at, assigned_agents
                FROM analysis_tasks
                WHERE user_id = ? AND status IN ('pending', 'processing')
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = await cursor.fetchall()
            
            for row in rows:
                assigned_agents = []
                if row[5]:
                    try:
                        agent_ids = json.loads(row[5])
                        for aid in agent_ids:
                            assigned_agents.append({
                                "id": aid,
                                "name": f"智能体_{aid[:8]}",
                                "avatar": None
                            })
                    except:
                        pass
                
                progress = 0.5 if row[3] == "processing" else 0.0
                
                tasks.append(TaskInfo(
                    id=row[0],
                    type=row[1] or "analysis",
                    description=row[2][:100] if row[2] else "任务处理中",
                    status=row[3],
                    progress=progress,
                    assigned_agents=assigned_agents,
                    start_time=str(row[4])
                ))
            
            break
        finally:
            await conn.close()
    
    return {
        "tasks": [t.dict() for t in tasks],
        "total": len(tasks)
    }


@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取仪表盘统计数据
    """
    user_id = current_user["id"]
    
    stats = {
        "total_agents": 6,
        "online_agents": 6,
        "busy_agents": 0,
        "idle_agents": 6,
        "today_tasks": 0,
        "completed_tasks": 0,
        "today_points": 0,
        "total_points": 0,
    }
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM user_agents WHERE user_id = ?
            """, (user_id,))
            row = await cursor.fetchone()
            if row and row[0]:
                stats["total_agents"] = row[0]
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM analysis_tasks 
                WHERE user_id = ? AND DATE(created_at) = DATE('now')
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                stats["today_tasks"] = row[0]
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM analysis_tasks 
                WHERE user_id = ? AND status = 'completed'
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                stats["completed_tasks"] = row[0]
            
            try:
                cursor = await conn.execute("""
                    SELECT integral FROM users WHERE id = ?
                """, (user_id,))
                row = await cursor.fetchone()
                if row:
                    stats["total_points"] = row[0] or 0
            except:
                pass
            
            break
        finally:
            await conn.close()
    
    return stats


@router.get("/task-assignment-options")
async def get_task_assignment_options(
    task_type: str = Query("analysis"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取任务分配选项（可用智能体列表及推荐）
    """
    user_id = current_user["id"]
    recommendations = []
    
    task_dept_mapping = {
        "analysis": ["gong", "bing", "li"],
        "consult": ["li_guan", "li"],
        "data_collection": ["bing", "hu"],
        "report": ["gong", "hu"],
        "security": ["xing"],
    }
    
    preferred_depts = task_dept_mapping.get(task_type, [])
    
    agents = await _get_default_agents(user_id)
    
    for agent in agents:
        score = 0.5
        reason = "可用"
        
        if agent.department in preferred_depts:
            score = 0.9
            reason = "专业匹配"
        elif agent.status == "idle":
            score = 0.7
            reason = "空闲可用"
        elif agent.status == "busy":
            score = 0.3
            reason = "当前忙碌"
        
        recommendations.append(AgentRecommendation(
            agent_id=agent.id,
            agent_name=agent.name,
            department=agent.department,
            score=score,
            reason=reason
        ))
    
    recommendations.sort(key=lambda x: x.score, reverse=True)
    
    return {
        "task_type": task_type,
        "recommendations": [r.dict() for r in recommendations],
        "auto_assign_recommendation": [r.agent_id for r in recommendations[:3] if r.score > 0.5]
    }


@router.post("/start-task")
async def start_task(
    request: TaskStartRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    启动新任务
    """
    user_id = current_user["id"]
    
    import uuid
    task_id = str(uuid.uuid4())
    
    if request.auto_assign and not request.agent_ids:
        options = await get_task_assignment_options(request.task_type, current_user)
        request.agent_ids = options.get("auto_assign_recommendation", [])
    
    async for conn in get_db_connection():
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_tasks (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_type TEXT,
                    input TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    assigned_agents TEXT
                )
            """)
            
            await conn.execute("""
                INSERT INTO user_tasks (id, user_id, task_type, input, status, assigned_agents)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (
                task_id,
                user_id,
                request.task_type,
                request.input,
                json.dumps(request.agent_ids) if request.agent_ids else None
            ))
            
            if request.agent_ids:
                for agent_id in request.agent_ids:
                    await conn.execute("""
                        UPDATE user_agents 
                        SET status = 'busy', 
                            current_task_id = ?,
                            current_task_type = 'user_task',
                            work_start_time = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (task_id, agent_id, user_id))
            
            break
        finally:
            await conn.close()
    
    await _broadcast_status_update(user_id, {
        "type": "task_started",
        "task_id": task_id,
        "task_type": request.task_type,
        "assigned_agents": request.agent_ids or []
    })
    
    return {
        "success": True,
        "task_id": task_id,
        "status": "pending",
        "assigned_agents": request.agent_ids or []
    }


@router.get("/logs")
async def get_agent_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取智能体工作日志
    """
    user_id = current_user["id"]
    logs = []
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT id, agent_name, action, created_at
                FROM agent_work_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = await cursor.fetchall()
            logs = [
                {
                    "id": row[0],
                    "agent_name": row[1],
                    "action": row[2],
                    "timestamp": str(row[3])
                }
                for row in rows
            ]
            
        except:
            logs = _generate_mock_logs()
            break
        finally:
            await conn.close()
    
    if not logs:
        logs = _generate_mock_logs()
    
    return {
        "logs": logs,
        "total": len(logs)
    }


def _generate_mock_logs() -> List[Dict]:
    actions = [
        ("吏部", "检查用户权限配置"),
        ("户部", "统计今日积分消耗"),
        ("礼部", "处理用户咨询请求"),
        ("兵部", "采集深圳房价数据"),
        ("刑部", "扫描系统安全状态"),
        ("工部", "生成分析报告"),
    ]
    
    logs = []
    for i, (agent, action) in enumerate(actions):
        logs.append({
            "id": f"log_{i}",
            "agent_name": agent,
            "action": action,
            "timestamp": (datetime.now() - timedelta(minutes=i * 5)).isoformat()
        })
    
    return logs


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket实时推送
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _broadcast_status_update(user_id: str, message: dict):
    """
    广播状态更新
    """
    message["timestamp"] = datetime.now().isoformat()
    message["user_id"] = user_id
    await manager.broadcast(message)


async def update_agent_status(
    user_id: str,
    agent_id: str,
    status: str,
    task_id: str = None,
    task_type: str = None
):
    """
    更新智能体状态（供其他模块调用）
    """
    async for conn in get_db_connection():
        try:
            if status == "idle":
                await conn.execute("""
                    UPDATE user_agents 
                    SET status = 'idle',
                        current_task_id = NULL,
                        current_task_type = NULL,
                        work_start_time = NULL
                    WHERE id = ? AND user_id = ?
                """, (agent_id, user_id))
            else:
                await conn.execute("""
                    UPDATE user_agents 
                    SET status = ?,
                        current_task_id = ?,
                        current_task_type = ?,
                        work_start_time = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (status, task_id, task_type, agent_id, user_id))
            
            await _broadcast_status_update(user_id, {
                "type": "agent_status_update",
                "agent_id": agent_id,
                "status": status,
                "task_id": task_id
            })
            
            break
        finally:
            await conn.close()
