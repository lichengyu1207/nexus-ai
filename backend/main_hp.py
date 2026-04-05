"""
高性能FastAPI应用入口
整合所有高性能服务和中间件
"""
import os
import sys
import time
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .services.high_performance import (
    init_high_performance,
    get_hp_service,
    lifespan_context
)
from .services.fault_tolerance import (
    ExceptionMiddleware,
    GracefulShutdown,
    AppException,
    init_fault_tolerance
)
from .services.monitoring import (
    init_monitoring,
    get_monitoring,
    MetricsConfig
)
from .services.api import (
    init_rate_limiter,
    CircuitBreakerRegistry
)
from .services.cache import init_cache
from .services.queue import init_task_queue
from .services.database import init_db_service

logger = logging.getLogger(__name__)


def setup_logging():
    """配置日志"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    for noisy_logger in ["uvicorn.access", "asyncio"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def create_app(
    title: str = "房都督平台",
    description: str = "高并发、高性能、无报错架构",
    version: str = "1.0.0",
    enable_docs: bool = True
) -> FastAPI:
    """创建高性能FastAPI应用"""
    
    setup_logging()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Initializing high performance services...")
        
        try:
            results = await init_high_performance()
            logger.info(f"Services initialized: {results}")
            
            yield
            
        finally:
            shutdown = GracefulShutdown.get_instance()
            await shutdown.shutdown()
            logger.info("Application shutdown completed")
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    app.add_middleware(ExceptionMiddleware)
    
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
    
    @app.middleware("http")
    async def add_trace_id(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
        request.state.trace_id = trace_id
        
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        
        return response
    
    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
            return await call_next(request)
        
        monitoring = get_monitoring()
        
        start_time = time.time()
        
        monitoring._metrics.start_http_request(
            request.method,
            request.url.path
        )
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            monitoring.record_http_request(
                request.method,
                request.url.path,
                response.status_code,
                duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            monitoring.record_http_request(
                request.method,
                request.url.path,
                500,
                duration
            )
            monitoring.record_error(type(e).__name__, request.url.path)
            raise
        finally:
            monitoring._metrics.end_http_request(
                request.method,
                request.url.path
            )
    
    from .routers.high_performance_router import include_router
    include_router(app)
    
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "房都督平台",
            "version": version,
            "status": "running",
            "docs": "/docs" if enable_docs else None
        }
    
    @app.get("/health", tags=["Health"])
    async def health():
        from .services.fault_tolerance import get_health_status
        status = await get_health_status()
        
        if not status.get("healthy", False):
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "checks": status.get("checks", {})}
            )
        
        return {"status": "healthy", "checks": status.get("checks", {})}
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        from .services.high_performance import get_all_metrics
        metrics_data = await get_all_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4"
        )
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        )
    
    return app


def generate_trace_id() -> str:
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:16]


app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 1,
    reload: bool = False
):
    """运行服务器"""
    import uvicorn
    
    uvicorn.run(
        "backend.main_hp:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
