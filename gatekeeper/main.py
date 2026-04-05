"""
主入口 - 启动心跳扫描器和 API 服务
"""
import asyncio
import logging
import sys
from typing import Optional

from .config import settings
from .scanner import HeartbeatScanner
from .restarter import Restarter
from .api import app, set_scanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class Gatekeeper:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.restarter: Optional[Restarter] = None
        self.scanner: Optional[HeartbeatScanner] = None
        self._running = False

    async def start(self):
        logger.info("Starting Gatekeeper...")

        if not HAS_REDIS:
            logger.error("redis package not installed")
            raise RuntimeError("redis package is required")

        self.redis_client = await redis.from_url(
            settings.redis_url, decode_responses=True
        )
        logger.info(f"Connected to Redis: {settings.redis_url}")

        self.restarter = Restarter(
            settings.restart_command_template, settings.restart_cooling
        )

        self.scanner = HeartbeatScanner(self.redis_client, self.restarter)
        set_scanner(self.scanner)

        self._running = True
        logger.info("Gatekeeper initialized successfully")

    async def stop(self):
        logger.info("Stopping Gatekeeper...")
        self._running = False

        if self.scanner:
            self.scanner.stop()

        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection closed")

        logger.info("Gatekeeper stopped")

    async def run_scanner(self):
        if self.scanner:
            await self.scanner.run()


async def main():
    gatekeeper = Gatekeeper()
    await gatekeeper.start()

    scan_task = asyncio.create_task(gatekeeper.run_scanner())

    import uvicorn
    config = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except asyncio.CancelledError:
        pass
    finally:
        scan_task.cancel()
        await gatekeeper.stop()


if __name__ == "__main__":
    asyncio.run(main())
