"""
Prometheus监控集成
"""
import os
from fastapi import FastAPI

from ..logger import get_logger

logger = get_logger("prometheus")

PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"


def setup_prometheus(app: FastAPI):
    """设置Prometheus监控"""
    if not PROMETHEUS_ENABLED:
        logger.info("Prometheus metrics disabled")
        return
    
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.warning("prometheus_fastapi_instrumentator not installed, metrics disabled")
