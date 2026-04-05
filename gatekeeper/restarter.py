"""
重启执行器 - 执行重启命令并管理冷却时间
"""
import asyncio
import time
import logging
from typing import Dict, Optional, Tuple
from .config import settings
from .models import TriggerType, RestartResult

logger = logging.getLogger(__name__)


class Restarter:
    def __init__(self, command_template: str, cooling_seconds: int):
        self.command_template = command_template
        self.cooling_seconds = cooling_seconds
        self._last_restart_time: Dict[str, float] = {}
        self._restart_count: Dict[str, int] = {}

    def _decode_output(self, data: bytes) -> str:
        try:
            return data.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return data.decode("gbk", errors="replace").strip()
            except Exception:
                return data.decode("utf-8", errors="replace").strip()

    def is_in_cooling(self, agent_id: str) -> Tuple[bool, float]:
        now = time.time()
        if agent_id in self._last_restart_time:
            elapsed = now - self._last_restart_time[agent_id]
            if elapsed < self.cooling_seconds:
                return True, self.cooling_seconds - elapsed
        return False, 0.0

    async def restart(
        self,
        agent_id: str,
        trigger: str = "auto",
        operator: Optional[str] = None,
        last_heartbeat: Optional[float] = None,
    ) -> bool:
        now = time.time()
        in_cooling, remaining = self.is_in_cooling(agent_id)
        if in_cooling:
            logger.warning(
                f"Agent {agent_id} in cooling period, {remaining:.1f}s remaining"
            )
            return False

        command = self.command_template.format(agent_id=agent_id)
        logger.info(f"Executing restart command for {agent_id}: {command}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully restarted agent {agent_id}")
                self._last_restart_time[agent_id] = now
                self._restart_count[agent_id] = self._restart_count.get(agent_id, 0) + 1
                await self._log_restart(
                    agent_id,
                    trigger,
                    operator,
                    last_heartbeat,
                    success=True,
                )
                return True
            else:
                error_msg = self._decode_output(stderr) if stderr else "Unknown error"
                logger.error(f"Failed to restart agent {agent_id}: {error_msg}")
                await self._log_restart(
                    agent_id,
                    trigger,
                    operator,
                    last_heartbeat,
                    success=False,
                    error=error_msg,
                )
                return False

        except Exception as e:
            logger.exception(f"Exception while restarting agent {agent_id}: {e}")
            await self._log_restart(
                agent_id,
                trigger,
                operator,
                last_heartbeat,
                success=False,
                error=str(e),
            )
            return False

    async def _log_restart(
        self,
        agent_id: str,
        trigger: str,
        operator: Optional[str],
        last_heartbeat: Optional[float],
        success: bool,
        error: str = "",
    ):
        from .logger import log_restart_event

        await log_restart_event(
            agent_id=agent_id,
            trigger=trigger,
            operator=operator,
            last_heartbeat=last_heartbeat,
            success=success,
            error=error,
        )

    def get_restart_count(self, agent_id: str) -> int:
        return self._restart_count.get(agent_id, 0)

    def reset_cooling(self, agent_id: str):
        if agent_id in self._last_restart_time:
            del self._last_restart_time[agent_id]
