"""
FastAPI 路由 - 提供手动重启接口和状态查询
"""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    RestartRequest,
    RestartResponse,
    HealthResponse,
    RestartEvent,
)
from .logger import get_recent_events

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gatekeeper API",
    description="智能体死循环/卡死检测与自动重启模块 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_restarter_instance = None
_scanner_instance = None


def get_restarter():
    global _restarter_instance
    if _restarter_instance is None:
        from .restarter import Restarter

        _restarter_instance = Restarter(
            settings.restart_command_template, settings.restart_cooling
        )
    return _restarter_instance


def get_scanner():
    return _scanner_instance


def set_scanner(scanner):
    global _scanner_instance
    _scanner_instance = scanner


@app.get("/api/admin/health", response_model=HealthResponse)
async def health():
    scanner = get_scanner()
    redis_connected = True
    if scanner and hasattr(scanner, "redis"):
        try:
            await scanner.redis.ping()
        except Exception:
            redis_connected = False

    return HealthResponse(
        status="ok",
        redis_connected=redis_connected,
    )


@app.post("/api/admin/agents/{agent_id}/restart", response_model=RestartResponse)
async def manual_restart(
    agent_id: str,
    request: Optional[RestartRequest] = None,
    restarter=Depends(get_restarter),
):
    logger.info(f"Manual restart requested for agent {agent_id}")

    operator = request.operator if request else "admin"

    result = await restarter.restart(
        agent_id,
        trigger="manual",
        operator=operator,
    )

    if result:
        return RestartResponse(
            status="success",
            message=f"Restart command sent for agent {agent_id}",
            agent_id=agent_id,
        )
    else:
        in_cooling, remaining = restarter.is_in_cooling(agent_id)
        if in_cooling:
            raise HTTPException(
                status_code=429,
                detail=f"Agent {agent_id} is in cooling period, {remaining:.1f}s remaining",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart agent {agent_id}",
        )


@app.get("/api/admin/agents/status")
async def get_all_agent_status(scanner=Depends(get_scanner)):
    if not scanner:
        raise HTTPException(status_code=503, detail="Scanner not initialized")
    return scanner.get_all_status()


@app.get("/api/admin/agents/{agent_id}/status")
async def get_agent_status(agent_id: str, scanner=Depends(get_scanner)):
    if not scanner:
        raise HTTPException(status_code=503, detail="Scanner not initialized")

    status = scanner.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return status


@app.get("/api/admin/restart-logs", response_model=list[RestartEvent])
async def get_restart_logs(limit: int = Query(default=100, le=1000)):
    events = await get_recent_events(limit)
    return events


@app.post("/api/admin/agents/{agent_id}/reset-cooling")
async def reset_cooling(agent_id: str, restarter=Depends(get_restarter)):
    restarter.reset_cooling(agent_id)
    return {"status": "success", "message": f"Cooling reset for agent {agent_id}"}
