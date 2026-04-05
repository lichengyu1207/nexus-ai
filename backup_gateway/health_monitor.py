"""
健康监控器 - 监控网关和服务状态
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        latency_ms: float = 0,
        timestamp: Optional[datetime] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.latency_ms = latency_ms
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthMonitor:
    def __init__(
        self,
        check_interval: int = 10,
        unhealthy_threshold: int = 3,
        healthy_threshold: int = 2,
    ):
        self.check_interval = check_interval
        self.unhealthy_threshold = unhealthy_threshold
        self.healthy_threshold = healthy_threshold
        self._checks: Dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}
        self._results: Dict[str, List[HealthCheckResult]] = {}
        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_successes: Dict[str, int] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[str, HealthStatus], Awaitable[None]]] = []

    def register_check(self, name: str, check_func: Callable[[], Awaitable[HealthCheckResult]]):
        self._checks[name] = check_func
        self._results[name] = []
        self._consecutive_failures[name] = 0
        self._consecutive_successes[name] = 0

    def register_callback(self, callback: Callable[[str, HealthStatus], Awaitable[None]]):
        self._callbacks.append(callback)

    async def run_check(self, name: str) -> HealthCheckResult:
        check_func = self._checks.get(name)
        if not check_func:
            return HealthCheckResult(name, HealthStatus.UNKNOWN, "Check not registered")

        start_time = time.time()
        try:
            result = await check_func()
            result.latency_ms = (time.time() - start_time) * 1000
        except Exception as e:
            result = HealthCheckResult(
                name,
                HealthStatus.UNHEALTHY,
                str(e),
                (time.time() - start_time) * 1000,
            )

        self._results[name].append(result)
        if len(self._results[name]) > 100:
            self._results[name] = self._results[name][-100:]

        await self._update_status(name, result.status)
        return result

    async def _update_status(self, name: str, status: HealthStatus):
        if status == HealthStatus.HEALTHY:
            self._consecutive_failures[name] = 0
            self._consecutive_successes[name] += 1
        else:
            self._consecutive_successes[name] = 0
            self._consecutive_failures[name] += 1

        current_status = self.get_status(name)
        for callback in self._callbacks:
            try:
                await callback(name, current_status)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_status(self, name: str) -> HealthStatus:
        failures = self._consecutive_failures.get(name, 0)
        successes = self._consecutive_successes.get(name, 0)

        if failures >= self.unhealthy_threshold:
            return HealthStatus.UNHEALTHY
        elif successes >= self.healthy_threshold:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    async def _monitor_loop(self):
        while self._running:
            for name in self._checks:
                try:
                    await self.run_check(name)
                except Exception as e:
                    logger.error(f"Health check error for {name}: {e}")

            await asyncio.sleep(self.check_interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Health monitor stopped")

    def get_results(self, name: Optional[str] = None) -> Dict[str, Any]:
        if name:
            return {
                "status": self.get_status(name).value,
                "results": [r.to_dict() for r in self._results.get(name, [])],
            }

        return {
            name: {
                "status": self.get_status(name).value,
                "results": [r.to_dict() for r in results[-10:]],
            }
            for name, results in self._results.items()
        }


async def check_http_endpoint(url: str, timeout: int = 5) -> HealthCheckResult:
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if 200 <= response.status < 300:
                    return HealthCheckResult(
                        f"http:{url}",
                        HealthStatus.HEALTHY,
                        f"Status: {response.status}",
                    )
                else:
                    return HealthCheckResult(
                        f"http:{url}",
                        HealthStatus.UNHEALTHY,
                        f"Status: {response.status}",
                    )
    except Exception as e:
        return HealthCheckResult(f"http:{url}", HealthStatus.UNHEALTHY, str(e))


async def check_tcp_port(host: str, port: int, timeout: int = 5) -> HealthCheckResult:
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return HealthCheckResult(
                f"tcp:{host}:{port}",
                HealthStatus.HEALTHY,
                "Port is open",
            )
        else:
            return HealthCheckResult(
                f"tcp:{host}:{port}",
                HealthStatus.UNHEALTHY,
                "Port is closed",
            )
    except Exception as e:
        return HealthCheckResult(f"tcp:{host}:{port}", HealthStatus.UNHEALTHY, str(e))


async def check_process(process_name: str) -> HealthCheckResult:
    import psutil

    try:
        for proc in psutil.process_iter(["name"]):
            if process_name.lower() in proc.info["name"].lower():
                return HealthCheckResult(
                    f"process:{process_name}",
                    HealthStatus.HEALTHY,
                    f"Process {process_name} is running",
                )
        return HealthCheckResult(
            f"process:{process_name}",
            HealthStatus.UNHEALTHY,
            f"Process {process_name} not found",
        )
    except Exception as e:
        return HealthCheckResult(f"process:{process_name}", HealthStatus.UNHEALTHY, str(e))
