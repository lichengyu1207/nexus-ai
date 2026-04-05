"""
心跳扫描器 - 定期扫描 Redis 中的心跳记录，检测失联智能体
"""
import asyncio
import time
import logging
import json
from typing import Set, Optional
from .config import settings
from .restarter import Restarter

logger = logging.getLogger(__name__)


class HeartbeatScanner:
    def __init__(self, redis_client, restarter: Restarter):
        self.redis = redis_client
        self.restarter = restarter
        self._running = True
        self._pending_restarts: Set[str] = set()
        self._agent_status: dict = {}

    async def run(self):
        logger.info("Heartbeat scanner started")
        while self._running:
            try:
                await self.scan()
            except Exception as e:
                logger.exception(f"Scan error: {e}")
            await asyncio.sleep(settings.scan_interval)
        logger.info("Heartbeat scanner stopped")

    async def scan(self):
        keys = await self.redis.keys("agent:*:heartbeat")
        now = time.time()

        for key in keys:
            agent_id = self._extract_agent_id(key)
            if not agent_id:
                continue

            data = await self.redis.get(key)
            if not data:
                self._update_status(agent_id, None, False)
                continue

            try:
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                heartbeat = json.loads(data)
                last_ts = heartbeat.get("timestamp")

                if last_ts is None:
                    self._update_status(agent_id, None, False)
                    continue

                is_alive = (now - last_ts) <= settings.heartbeat_timeout
                self._update_status(agent_id, last_ts, is_alive)

                if not is_alive:
                    await self._handle_timeout(agent_id, last_ts)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid heartbeat data for {agent_id}: {e}")
                self._update_status(agent_id, None, False)
            except Exception as e:
                logger.error(f"Error processing {key}: {e}")

    def _extract_agent_id(self, key) -> Optional[str]:
        try:
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            parts = key.split(":")
            if len(parts) >= 2:
                return parts[1]
        except Exception:
            pass
        return None

    def _update_status(self, agent_id: str, last_heartbeat: Optional[float], is_alive: bool):
        self._agent_status[agent_id] = {
            "last_heartbeat": last_heartbeat,
            "is_alive": is_alive,
            "last_check": time.time(),
        }

    async def _handle_timeout(self, agent_id: str, last_heartbeat: float):
        if agent_id in self._pending_restarts:
            logger.debug(f"Agent {agent_id} already pending restart")
            return

        in_cooling, remaining = self.restarter.is_in_cooling(agent_id)
        if in_cooling:
            logger.debug(
                f"Agent {agent_id} in cooling period, {remaining:.1f}s remaining"
            )
            return

        logger.warning(
            f"Agent {agent_id} heartbeat timeout, last at {last_heartbeat}"
        )
        self._pending_restarts.add(agent_id)
        asyncio.create_task(self._restart_with_cleanup(agent_id, last_heartbeat))

    async def _restart_with_cleanup(self, agent_id: str, last_heartbeat: float):
        try:
            await self.restarter.restart(
                agent_id,
                trigger="auto",
                last_heartbeat=last_heartbeat,
            )
        except Exception as e:
            logger.exception(f"Restart failed for {agent_id}: {e}")
        finally:
            self._pending_restarts.discard(agent_id)

    def stop(self):
        self._running = False

    def get_agent_status(self, agent_id: str) -> Optional[dict]:
        return self._agent_status.get(agent_id)

    def get_all_status(self) -> dict:
        return self._agent_status.copy()
