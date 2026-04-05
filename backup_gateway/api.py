"""
FastAPI 接口 - 网关管理 API
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from .config import settings
from .gateway import BackupGateway
from .health_monitor import HealthMonitor, HealthStatus
from .keepalived_manager import KeepalivedManager, KeepalivedState
from .notifier import FailoverNotifier, FailoverEvent, NodeState

app = FastAPI(
    title="Backup Gateway API",
    description="高可用备用网关管理接口",
    version="1.0.0",
)

gateway = BackupGateway()
health_monitor = HealthMonitor()
keepalived = KeepalivedManager()
notifier = FailoverNotifier()


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class GatewayStatsResponse(BaseModel):
    running: bool
    port: int
    backend_url: str
    start_time: Optional[str]
    uptime_seconds: float
    request_count: int
    error_count: int


class KeepalivedStatsResponse(BaseModel):
    running: bool
    state: str
    has_vip: bool
    vip: str
    interface: str
    priority: int
    last_check: Optional[str]


class FailoverRequest(BaseModel):
    old_state: str
    new_state: str
    vip: str
    reason: str = ""


class ConfigUpdateRequest(BaseModel):
    backend_url: Optional[str] = None
    port: Optional[int] = None
    vip: Optional[str] = None
    priority: Optional[int] = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if gateway.is_healthy() else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/ready")
async def readiness_check():
    if not gateway.is_healthy():
        raise HTTPException(status_code=503, detail="Gateway not ready")
    return {"status": "ready"}


@app.get("/stats/gateway", response_model=GatewayStatsResponse)
async def get_gateway_stats():
    stats = gateway.get_stats()
    return GatewayStatsResponse(**stats)


@app.get("/stats/keepalived", response_model=KeepalivedStatsResponse)
async def get_keepalived_stats():
    stats = keepalived.get_stats()
    return KeepalivedStatsResponse(**stats)


@app.get("/stats/health")
async def get_health_stats():
    return health_monitor.get_results()


@app.get("/stats/failover")
async def get_failover_history():
    return {"events": notifier.get_history()}


@app.post("/failover/notify")
async def trigger_failover_notification(request: FailoverRequest):
    event = FailoverEvent(
        old_state=NodeState(request.old_state.upper()),
        new_state=NodeState(request.new_state.upper()),
        vip=request.vip,
        reason=request.reason,
    )
    success = await notifier.notify(event)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")
    return {"status": "notified", "event": event.to_dict()}


@app.post("/gateway/start")
async def start_gateway():
    if gateway._running:
        raise HTTPException(status_code=400, detail="Gateway already running")
    gateway.start()
    return {"status": "started"}


@app.post("/gateway/stop")
async def stop_gateway():
    gateway.stop()
    return {"status": "stopped"}


@app.post("/keepalived/restart")
async def restart_keepalived():
    success = await keepalived.restart()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restart keepalived")
    return {"status": "restarted"}


@app.get("/keepalived/config")
async def get_keepalived_config():
    return {"config": keepalived.generate_config()}


@app.get("/vip")
async def check_vip():
    return {
        "has_vip": keepalived.has_vip(),
        "vip": settings.VIP,
        "interface": settings.INTERFACE,
    }


@app.get("/config")
async def get_config():
    return {
        "port": settings.PORT,
        "backend_url": settings.BACKEND_URL,
        "vip": settings.VIP,
        "interface": settings.INTERFACE,
        "priority": settings.PRIORITY,
        "state": settings.STATE,
        "check_interval": settings.CHECK_INTERVAL,
    }


def run_api():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18791)


if __name__ == "__main__":
    run_api()
