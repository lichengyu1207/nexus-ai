"""
安全防护API路由
Security Protection API Router

提供安全监控、攻击分析、封禁管理等REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time

from ..agents.security import (
    patrol_agent, judge_agent, prison_agent, coroner_agent,
    security_kernel, ThreatLevel, AttackType, SecurityAction
)
from ..agents.security.federated import parameter_server


router = APIRouter(prefix="/api/security", tags=["security"])


class RequestRecord(BaseModel):
    ip: str
    url: str
    method: str = "GET"
    status_code: int = 200
    user_agent: str = ""
    packet_size: int = 0
    response_time: float = 0.0
    geo_location: str = ""


class UnbanRequest(BaseModel):
    ip: str
    reason: str = "manual"


class TrainRequest(BaseModel):
    decision_id: str
    effect: Dict[str, Any]
    next_features: Optional[Dict] = None


@router.get("/status")
async def get_security_status():
    """获取安全系统状态"""
    try:
        status = security_kernel.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patrol/status")
async def get_patrol_status():
    """获取巡捕智能体状态"""
    return patrol_agent.get_status()


@router.get("/judge/status")
async def get_judge_status():
    """获取判官智能体状态"""
    return judge_agent.get_status()


@router.get("/prison/status")
async def get_prison_status():
    """获取牢头智能体状态"""
    return prison_agent.get_status()


@router.get("/coroner/status")
async def get_coroner_status():
    """获取仵作智能体状态"""
    return coroner_agent.get_status()


@router.post("/record")
async def record_request(request: RequestRecord):
    """记录请求"""
    try:
        security_kernel.record_request(
            ip=request.ip,
            url=request.url,
            method=request.method,
            status_code=request.status_code,
            user_agent=request.user_agent,
            packet_size=request.packet_size,
            response_time=request.response_time,
            geo_location=request.geo_location
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bans")
async def get_ban_list():
    """获取封禁列表"""
    return {
        "bans": prison_agent.get_ban_list(),
        "total": len(prison_agent._ban_records)
    }


@router.post("/unban")
async def unban_ip(request: UnbanRequest):
    """解封IP"""
    success = await prison_agent.unban_ip(request.ip, request.reason)
    return {"success": success}


@router.get("/executions")
async def get_execution_history(limit: int = Query(100, ge=1, le=1000)):
    """获取执行历史"""
    return {
        "executions": prison_agent.get_recent_executions(limit),
        "total": len(prison_agent._execution_history)
    }


@router.get("/reports")
async def get_attack_reports(limit: int = Query(20, ge=1, le=100)):
    """获取攻击报告"""
    return {
        "reports": coroner_agent.get_recent_reports(limit),
        "total": len(coroner_agent._attack_reports)
    }


@router.post("/train")
async def train_from_experience(request: TrainRequest, background_tasks: BackgroundTasks):
    """从经验中学习"""
    try:
        from ..agents.security.patrol_agent import TrafficFeatures
        
        next_features = None
        if request.next_features:
            next_features = TrafficFeatures.from_dict(request.next_features)
        
        loss = await judge_agent.learn_from_experience(
            request.decision_id,
            request.effect,
            next_features
        )
        
        return {
            "success": True,
            "loss": loss,
            "buffer_size": len(judge_agent.rl_agent.buffer)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "epsilon": judge_agent.rl_agent.epsilon,
        "training_step": judge_agent.rl_agent.training_step,
        "buffer_size": len(judge_agent.rl_agent.buffer),
        "device": str(judge_agent.rl_agent.device)
    }


@router.post("/model/save")
async def save_model(path: str = "security_model.pt"):
    """保存模型"""
    try:
        judge_agent.rl_agent.save_model(path)
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/load")
async def load_model(path: str = "security_model.pt"):
    """加载模型"""
    try:
        judge_agent.rl_agent.load_model(path)
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/federated/status")
async def get_federated_status():
    """获取联邦学习状态"""
    return parameter_server.get_status()


@router.post("/federated/register")
async def register_federated_node(node_id: str, node_info: Dict = None):
    """注册联邦学习节点"""
    success = await parameter_server.register_node(node_id, node_info or {})
    return {"success": success}


@router.get("/federated/model")
async def get_global_model():
    """获取全局模型"""
    return await parameter_server.get_global_model()


@router.get("/statistics")
async def get_security_statistics(days: int = Query(7, ge=1, le=30)):
    """获取安全统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT stat_date, total_requests, blocked_requests, 
                           captcha_challenges, rate_limited, attacks_detected,
                           attacks_blocked, false_positives
                    FROM security_statistics
                    WHERE stat_date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY stat_date DESC
                """ % days)
                
                stats = [dict(row) for row in rows]
                
                return {
                    "statistics": stats,
                    "days": days
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_security_events(
    limit: int = Query(50, ge=1, le=200),
    threat_level: Optional[str] = None,
    attack_type: Optional[str] = None
):
    """获取安全事件"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                query = """
                    SELECT event_id, event_type, threat_level, attack_type,
                           source_ips, confidence, detected_at, status
                    FROM security_events
                    WHERE 1=1
                """
                params = []
                
                if threat_level:
                    query += " AND threat_level = $1"
                    params.append(threat_level)
                
                if attack_type:
                    query += f" AND attack_type = ${len(params) + 1}"
                    params.append(attack_type)
                
                query += f" ORDER BY detected_at DESC LIMIT ${len(params) + 1}"
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                events = [dict(row) for row in rows]
                
                return {
                    "events": events,
                    "total": len(events)
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threat-levels")
async def get_threat_levels():
    """获取威胁等级列表"""
    return {
        "levels": [level.value for level in ThreatLevel]
    }


@router.get("/attack-types")
async def get_attack_types():
    """获取攻击类型列表"""
    return {
        "types": [t.value for t in AttackType]
    }


@router.get("/actions")
async def get_security_actions():
    """获取安全动作列表"""
    return {
        "actions": [action.name for action in SecurityAction]
    }


@router.post("/start")
async def start_security_kernel():
    """启动安全内核"""
    try:
        await security_kernel.start()
        return {"success": True, "message": "安全内核已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_security_kernel():
    """停止安全内核"""
    try:
        await security_kernel.stop()
        return {"success": True, "message": "安全内核已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "patrol": patrol_agent._running,
            "judge": judge_agent._running,
            "prison": prison_agent._running,
            "coroner": coroner_agent._running
        }
    }
