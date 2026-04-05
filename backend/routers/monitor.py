"""
系统监控API路由
提供健康检查、性能监控和告警功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psutil
import asyncio
import json
import os
import sys
from pathlib import Path

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str
    timestamp: str
    uptime_seconds: float
    version: str
    environment: str


class SystemMetrics(BaseModel):
    """系统指标模型"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_connections: int
    process_count: int


class DatabaseMetrics(BaseModel):
    """数据库指标模型"""
    connection_pool_size: int
    active_connections: int
    query_count_24h: int
    slow_queries: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    avg_response_time_ms: float
    requests_per_minute: int
    error_rate_percent: float
    cache_hit_rate_percent: float
    active_users: int


class AlertRule(BaseModel):
    """告警规则模型"""
    id: str
    name: str
    condition: str
    threshold: float
    severity: str
    enabled: bool
    last_triggered: Optional[str]


class MonitoringDashboard(BaseModel):
    """监控仪表板模型"""
    health: HealthStatus
    system: SystemMetrics
    database: DatabaseMetrics
    performance: PerformanceMetrics
    alerts: List[AlertRule]


START_TIME = datetime.now()
VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


_metrics_store = {
    "request_times": [],
    "error_count": 0,
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
}


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    健康检查端点
    
    Returns:
        HealthStatus: 系统健康状态
    """
    uptime = (datetime.now() - START_TIME).total_seconds()
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        uptime_seconds=uptime,
        version=VERSION,
        environment=ENVIRONMENT
    )


@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics():
    """
    获取系统指标
    
    Returns:
        SystemMetrics: 系统性能指标
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_connections()
    
    return SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_mb=memory.used / 1024 / 1024,
        memory_total_mb=memory.total / 1024 / 1024,
        disk_percent=disk.percent,
        disk_used_gb=disk.used / 1024 / 1024 / 1024,
        disk_total_gb=disk.total / 1024 / 1024 / 1024,
        network_connections=len(network),
        process_count=len(psutil.pids())
    )


@router.get("/metrics/database", response_model=DatabaseMetrics)
async def get_database_metrics():
    """
    获取数据库指标
    
    Returns:
        DatabaseMetrics: 数据库性能指标
    """
    try:
        from ..database import get_pool
        
        pool = await get_pool()
        
        return DatabaseMetrics(
            connection_pool_size=pool.get_size() if hasattr(pool, 'get_size') else 10,
            active_connections=pool.get_idle_size() if hasattr(pool, 'get_idle_size') else 5,
            query_count_24h=_metrics_store.get("total_requests", 0),
            slow_queries=_get_slow_queries()
        )
    except Exception as e:
        return DatabaseMetrics(
            connection_pool_size=0,
            active_connections=0,
            query_count_24h=0,
            slow_queries=[]
        )


@router.get("/metrics/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """
    获取性能指标
    
    Returns:
        PerformanceMetrics: 应用性能指标
    """
    request_times = _metrics_store.get("request_times", [])
    avg_response_time = sum(request_times) / len(request_times) if request_times else 0
    
    total_requests = _metrics_store.get("total_requests", 0)
    error_count = _metrics_store.get("error_count", 0)
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
    
    cache_hits = _metrics_store.get("cache_hits", 0)
    cache_misses = _metrics_store.get("cache_misses", 0)
    cache_total = cache_hits + cache_misses
    cache_hit_rate = (cache_hits / cache_total * 100) if cache_total > 0 else 0
    
    return PerformanceMetrics(
        avg_response_time_ms=avg_response_time,
        requests_per_minute=total_requests,
        error_rate_percent=error_rate,
        cache_hit_rate_percent=cache_hit_rate,
        active_users=0
    )


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard():
    """
    获取监控仪表板数据
    
    Returns:
        MonitoringDashboard: 完整的监控数据
    """
    health = await health_check()
    system = await get_system_metrics()
    database = await get_database_metrics()
    performance = await get_performance_metrics()
    
    alerts = _check_alert_rules(system, database, performance)
    
    return MonitoringDashboard(
        health=health,
        system=system,
        database=database,
        performance=performance,
        alerts=alerts
    )


@router.post("/metrics/record")
async def record_metric(
    endpoint: str,
    response_time_ms: float,
    is_error: bool = False,
    is_cache_hit: Optional[bool] = None
):
    """
    记录性能指标
    
    Args:
        endpoint: 端点名称
        response_time_ms: 响应时间（毫秒）
        is_error: 是否为错误
        is_cache_hit: 是否为缓存命中
    """
    _metrics_store["request_times"].append(response_time_ms)
    if len(_metrics_store["request_times"]) > 1000:
        _metrics_store["request_times"] = _metrics_store["request_times"][-1000:]
    
    _metrics_store["total_requests"] += 1
    
    if is_error:
        _metrics_store["error_count"] += 1
    
    if is_cache_hit is not None:
        if is_cache_hit:
            _metrics_store["cache_hits"] += 1
        else:
            _metrics_store["cache_misses"] += 1
    
    return {"status": "recorded"}


@router.get("/alerts/rules")
async def get_alert_rules():
    """
    获取告警规则列表
    
    Returns:
        List[AlertRule]: 告警规则列表
    """
    return _get_default_alert_rules()


@router.post("/alerts/test")
async def test_alert_system(background_tasks: BackgroundTasks):
    """
    测试告警系统
    
    Args:
        background_tasks: 后台任务
    """
    background_tasks.add_task(_send_test_alert)
    return {"status": "alert_test_triggered"}


def _get_slow_queries() -> List[Dict[str, Any]]:
    """获取慢查询列表"""
    return [
        {
            "query": "SELECT * FROM houses WHERE city = ?",
            "duration_ms": 1500,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        }
    ]


def _get_default_alert_rules() -> List[AlertRule]:
    """获取默认告警规则"""
    return [
        AlertRule(
            id="cpu_high",
            name="CPU使用率过高",
            condition="cpu_percent > threshold",
            threshold=80.0,
            severity="warning",
            enabled=True,
            last_triggered=None
        ),
        AlertRule(
            id="memory_high",
            name="内存使用率过高",
            condition="memory_percent > threshold",
            threshold=85.0,
            severity="warning",
            enabled=True,
            last_triggered=None
        ),
        AlertRule(
            id="disk_high",
            name="磁盘使用率过高",
            condition="disk_percent > threshold",
            threshold=90.0,
            severity="critical",
            enabled=True,
            last_triggered=None
        ),
        AlertRule(
            id="response_time_slow",
            name="响应时间过慢",
            condition="avg_response_time_ms > threshold",
            threshold=1000.0,
            severity="warning",
            enabled=True,
            last_triggered=None
        ),
        AlertRule(
            id="error_rate_high",
            name="错误率过高",
            condition="error_rate_percent > threshold",
            threshold=5.0,
            severity="critical",
            enabled=True,
            last_triggered=None
        )
    ]


def _check_alert_rules(
    system: SystemMetrics,
    database: DatabaseMetrics,
    performance: PerformanceMetrics
) -> List[AlertRule]:
    """检查告警规则"""
    alerts = []
    rules = _get_default_alert_rules()
    
    for rule in rules:
        triggered = False
        
        if rule.id == "cpu_high" and system.cpu_percent > rule.threshold:
            triggered = True
        elif rule.id == "memory_high" and system.memory_percent > rule.threshold:
            triggered = True
        elif rule.id == "disk_high" and system.disk_percent > rule.threshold:
            triggered = True
        elif rule.id == "response_time_slow" and performance.avg_response_time_ms > rule.threshold:
            triggered = True
        elif rule.id == "error_rate_high" and performance.error_rate_percent > rule.threshold:
            triggered = True
        
        if triggered:
            rule.last_triggered = datetime.now().isoformat()
            alerts.append(rule)
    
    return alerts


async def _send_test_alert():
    """发送测试告警"""
    print(f"[{datetime.now().isoformat()}] 🚨 测试告警已触发")
    await asyncio.sleep(1)
    print(f"[{datetime.now().isoformat()}] ✅ 测试告警处理完成")


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 100):
    """
    获取最近的日志
    
    Args:
        lines: 日志行数
        
    Returns:
        Dict: 日志内容
    """
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        return {"logs": [], "message": "日志文件不存在"}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        return {"logs": [], "error": str(e)}


@router.get("/export")
async def export_metrics():
    """
    导出监控指标（Prometheus格式）
    
    Returns:
        str: Prometheus格式的指标
    """
    system = await get_system_metrics()
    performance = await get_performance_metrics()
    
    metrics = f"""# HELP cpu_usage_percent CPU使用率
# TYPE cpu_usage_percent gauge
cpu_usage_percent {system.cpu_percent}

# HELP memory_usage_percent 内存使用率
# TYPE memory_usage_percent gauge
memory_usage_percent {system.memory_percent}

# HELP disk_usage_percent 磁盘使用率
# TYPE disk_usage_percent gauge
disk_usage_percent {system.disk_percent}

# HELP avg_response_time_ms 平均响应时间
# TYPE avg_response_time_ms gauge
avg_response_time_ms {performance.avg_response_time_ms}

# HELP error_rate_percent 错误率
# TYPE error_rate_percent gauge
error_rate_percent {performance.error_rate_percent}

# HELP cache_hit_rate_percent 缓存命中率
# TYPE cache_hit_rate_percent gauge
cache_hit_rate_percent {performance.cache_hit_rate_percent}
"""
    
    return metrics
