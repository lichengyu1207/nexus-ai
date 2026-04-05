"""
API性能监控中间件
记录请求响应时间和慢查询
"""
import time
import uuid
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from ..logger import get_logger
from ..database import get_db_connection

logger = get_logger("performance_middleware")

SLOW_REQUEST_THRESHOLD_MS = 500
CRITICAL_REQUEST_THRESHOLD_MS = 2000


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
            return await call_next(request)
        
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        await self._log_request(request, response, duration_ms, request_id)
        
        if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            await self._log_slow_query(request, response, duration_ms, request_id)
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response
    
    async def _log_request(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str,
    ):
        """记录请求日志"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        if duration_ms > CRITICAL_REQUEST_THRESHOLD_MS:
            logger.warning(f"Critical slow request: {log_data}")
        elif duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(f"Slow request: {log_data}")
        else:
            logger.info(f"Request: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
    
    async def _log_slow_query(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str,
    ):
        """记录慢查询到数据库"""
        try:
            async with get_db_connection() as db:
                await db.execute("""
                    INSERT INTO slow_queries (
                        endpoint, method, duration_ms, request_id,
                        user_id, params, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.url.path,
                    request.method,
                    duration_ms,
                    request_id,
                    getattr(request.state, "user_id", None),
                    str(request.query_params)[:500],
                    datetime.now(),
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log slow query: {e}")


async def update_api_stats(endpoint: str, method: str, duration_ms: float, is_error: bool = False):
    """更新API统计"""
    try:
        today = datetime.now().date()
        
        async with get_db_connection() as db:
            cursor = await db.execute("""
                SELECT id, total_requests, total_duration_ms, min_duration_ms, max_duration_ms, error_count
                FROM api_performance
                WHERE endpoint = ? AND method = ? AND date = ?
            """, (endpoint, method, today))
            
            row = await cursor.fetchone()
            
            if row:
                new_total = row[1] + 1
                new_duration = row[2] + duration_ms
                new_avg = new_duration / new_total
                new_min = min(row[3], duration_ms) if row[3] else duration_ms
                new_max = max(row[4], duration_ms)
                new_errors = row[5] + (1 if is_error else 0)
                
                await db.execute("""
                    UPDATE api_performance
                    SET total_requests = ?, total_duration_ms = ?, avg_duration_ms = ?,
                        min_duration_ms = ?, max_duration_ms = ?, error_count = ?
                    WHERE id = ?
                """, (new_total, new_duration, new_avg, new_min, new_max, new_errors, row[0]))
            else:
                await db.execute("""
                    INSERT INTO api_performance (
                        endpoint, method, total_requests, total_duration_ms, avg_duration_ms,
                        min_duration_ms, max_duration_ms, error_count, date
                    ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint, method, duration_ms, duration_ms, duration_ms,
                    duration_ms, 1 if is_error else 0, today
                ))
            
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to update API stats: {e}")


def get_performance_summary() -> dict:
    """获取性能摘要"""
    return {
        "slow_request_threshold_ms": SLOW_REQUEST_THRESHOLD_MS,
        "critical_request_threshold_ms": CRITICAL_REQUEST_THRESHOLD_MS,
    }
